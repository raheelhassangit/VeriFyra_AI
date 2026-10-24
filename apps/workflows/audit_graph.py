import json
import logging
import time
from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.agents.base import AgentContext, BaseAgent
from app.errors import AgentError, AgentNotImplemented
from app.schemas.audit import AgentStatus

logger = logging.getLogger(__name__)
MAX_RESULT_BYTES = 200_000


class AuditState(TypedDict, total=False):
    audit_id: str
    website: dict
    repository: dict
    documentation: dict
    verdict: dict


def _validate_result(result):
    if not isinstance(result, dict):
        raise AgentError("Agent returned an invalid result.")
    try:
        size = len(json.dumps(result))
    except (TypeError, ValueError):
        raise AgentError("Agent result is not JSON-serializable.") from None
    if size > MAX_RESULT_BYTES:
        raise AgentError("Agent result too large; store compact evidence references instead.")


def _make_node(agent: BaseAgent):
    key = agent.agent_type.value.lower()

    async def node(state: AuditState, config: RunnableConfig) -> dict:
        cfg = config["configurable"]
        run = cfg["run"]
        rec = run.agents[agent.agent_type]

        if agent.needs_any and not any(
            t in run.agents and run.agents[t].status == AgentStatus.COMPLETED for t in agent.needs_any
        ):
            rec.status = AgentStatus.SKIPPED
            rec.error_message = "Skipped: no upstream agent produced evidence."
            return {}

        run.stage = agent.agent_type.value
        rec.status = AgentStatus.RUNNING
        started = time.monotonic()
        out: dict = {}
        try:
            ctx = AgentContext(
                request=run.request, doc_path=run.doc_path,
                prior={k: v for k, v in state.items() if k != "audit_id"},
                gemma=cfg["gemma"], settings=cfg["settings"],
            )
            result = await agent.run(ctx)
            _validate_result(result)
            rec.status, rec.result, out = AgentStatus.COMPLETED, result, {key: result}
        except AgentNotImplemented as e:
            rec.status, rec.error_message = AgentStatus.SKIPPED, str(e)
        except AgentError as e:
            rec.status, rec.error_message = AgentStatus.FAILED, str(e)[:2000]
        except Exception:
            logger.exception("agent_crashed audit=%s agent=%s", run.audit_id, agent.agent_type.value)
            rec.status, rec.error_message = AgentStatus.FAILED, "Unexpected agent error."
        finally:
            rec.duration_ms = int((time.monotonic() - started) * 1000)
        return out

    return node


def build_audit_graph(agents: list[BaseAgent]):
    g = StateGraph(AuditState)
    prev = START
    for agent in agents:
        name = f"{agent.agent_type.value.lower()}_agent"  # must differ from the state key
        g.add_node(name, _make_node(agent))
        g.add_edge(prev, name)
        prev = name
    g.add_edge(prev, END)
    return g.compile()