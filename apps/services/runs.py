import asyncio
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.agents.base import BaseAgent
from app.config import Settings
from app.schemas.audit import AgentOut, AgentStatus as S, AgentType as T, AuditRequest, StatusOut
from app.workflows.audit_graph import build_audit_graph

logger = logging.getLogger(__name__)


@dataclass
class AgentRecord:
    agent_type: T
    status: S = S.PENDING
    result: dict = field(default_factory=dict)
    error_message: str = ""
    duration_ms: int | None = None


@dataclass
class RunRecord:
    request: AuditRequest
    doc_path: Path | None
    work_dir: Path
    agents: dict[T, AgentRecord]
    state: str = "RUNNING"
    stage: str = "QUEUED_IN_SERVICE"
    commit_sha: str = ""
    executive_summary: str = ""
    coverage_percentage: float | None = None
    overall_score: float | None = None
    error: str = ""
    task: asyncio.Task | None = None
    finished_at: float | None = None

    @property
    def audit_id(self) -> str:
        return str(self.request.audit_id)

    def to_status(self) -> StatusOut:
        return StatusOut(
            state=self.state, stage=self.stage[:100],
            agents=[AgentOut(agent_type=a.agent_type, status=a.status, result=a.result,
                             error_message=a.error_message[:2000], duration_ms=a.duration_ms)
                    for a in self.agents.values()],
            commit_sha=self.commit_sha, executive_summary=self.executive_summary,
            coverage_percentage=self.coverage_percentage, overall_score=self.overall_score,
            error=self.error[:2000],
        )


def _pct(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 100 else None


class RunManager:
    def __init__(self, settings: Settings, agents: list[BaseAgent], gemma):
        self.settings, self.gemma = settings, gemma
        self._types = [a.agent_type for a in agents]
        self._graph = build_audit_graph(agents)
        self._runs: dict[str, RunRecord] = {}
        self._sem = asyncio.Semaphore(settings.agent_max_concurrent_audits)

    # ---- queries ----
    def get(self, audit_id: str):
        return self._runs.get(audit_id)

    def lookup(self, request: AuditRequest):
        """Existing run that already satisfies this request (same or newer attempt)."""
        r = self._runs.get(str(request.audit_id))
        return r if r and r.request.attempt >= request.attempt else None

    def active_count(self) -> int:
        return sum(1 for r in self._runs.values() if r.state == "RUNNING")

    def at_capacity(self) -> bool:
        return self.active_count() >= self.settings.agent_max_pending_audits

    def work_dir_for(self, request: AuditRequest) -> Path:
        return self.settings.agent_work_dir / str(request.audit_id) / str(request.attempt)

    # ---- commands ----
    def submit(self, request: AuditRequest, doc_path: Path | None = None):
        self._evict_expired()
        if (existing := self.lookup(request)):
            return existing, False
        old = self._runs.get(str(request.audit_id))
        if old and old.task and not old.task.done():
            old.task.cancel()  # superseded by a newer attempt
        rec = RunRecord(request=request, doc_path=doc_path, work_dir=self.work_dir_for(request),
                        agents={t: AgentRecord(t) for t in self._types})
        self._runs[rec.audit_id] = rec
        rec.task = asyncio.create_task(self._run(rec), name=f"audit-{rec.audit_id}")
        rec.task.add_done_callback(lambda t, r=rec: self._on_done(r, t))
        return rec, True

    def cancel(self, audit_id: str):
        rec = self._runs.get(audit_id)
        if rec and rec.state == "RUNNING" and rec.task:
            rec.task.cancel()
        return rec

    async def shutdown(self):
        tasks = [r.task for r in self._runs.values() if r.task and not r.task.done()]
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    # ---- internals ----
    async def _run(self, rec: RunRecord):
        try:
            async with self._sem:
                rec.stage = "STARTING"
                async with asyncio.timeout(self.settings.agent_max_audit_seconds):
                    await self._graph.ainvoke(
                        {"audit_id": rec.audit_id},
                        config={"configurable": {"run": rec, "gemma": self.gemma, "settings": self.settings}},
                    )
            self._finish(rec)
        except asyncio.CancelledError:
            rec.state, rec.stage = "CANCELLED", "CANCELLED"
            self._close_open_agents(rec, "Cancelled.", running=S.SKIPPED)
        except TimeoutError:
            rec.state, rec.stage = "FAILED", "FAILED"
            rec.error = "Audit exceeded the maximum allowed duration."
            self._close_open_agents(rec, "Timed out.", running=S.FAILED)
        except Exception:
            logger.exception("audit_crashed audit=%s", rec.audit_id)
            rec.state, rec.stage, rec.error = "FAILED", "FAILED", "Unexpected internal error."
            self._close_open_agents(rec, "Audit aborted.", running=S.FAILED)

    def _finish(self, rec: RunRecord):
        def res(t):
            a = rec.agents.get(t)
            return a.result if a and a.status == S.COMPLETED else {}

        rec.stage = "DONE"
        rec.commit_sha = str(res(T.REPOSITORY).get("commit_sha", ""))[:64]
        verdict = res(T.VERDICT)
        rec.executive_summary = str(verdict.get("executive_summary", ""))
        rec.coverage_percentage = _pct(verdict.get("coverage_percentage"))
        rec.overall_score = _pct(verdict.get("overall_score"))
        if any(a.status == S.COMPLETED for a in rec.agents.values()):
            rec.state = "COMPLETED"
        else:
            rec.state = "FAILED"
            detail = "; ".join(f"{t.value}: {a.error_message}" for t, a in rec.agents.items() if a.error_message)
            rec.error = f"No agent completed successfully. {detail}"[:2000]

    @staticmethod
    def _close_open_agents(rec, message, running):
        for a in rec.agents.values():
            if a.status in (S.PENDING, S.RUNNING):
                a.status = running if a.status == S.RUNNING else S.SKIPPED
                a.error_message = message

    def _on_done(self, rec: RunRecord, task: asyncio.Task):
        if rec.state == "RUNNING":  # task ended without reaching its own handlers (e.g. cancelled before start)
            rec.state = "CANCELLED" if task.cancelled() else "FAILED"
            rec.stage = rec.state
            if not task.cancelled():
                rec.error = "Audit task ended unexpectedly."
            self._close_open_agents(rec, "Audit ended before this agent ran.", running=S.SKIPPED)
        rec.finished_at = time.monotonic()
        shutil.rmtree(rec.work_dir, ignore_errors=True)

    def _evict_expired(self):
        cutoff = time.monotonic() - self.settings.agent_run_ttl_seconds
        for k in [k for k, r in self._runs.items() if r.finished_at and r.finished_at < cutoff]:
            del self._runs[k]