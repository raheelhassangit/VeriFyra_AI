import secrets
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, Response, UploadFile
from pydantic import ValidationError

from app.schemas.audit import AcceptedOut, AuditRequest, StatusOut
from app.services.runs import RunManager

ALLOWED_DOC_EXT = {".md", ".txt", ".pdf", ".docx"}


def get_runs(request: Request) -> RunManager:
    return request.app.state.runs


def require_internal_token(request: Request, authorization: str | None = Header(default=None)):
    expected = request.app.state.settings.agent_service_token.encode()
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(token.strip().encode(), expected):
        raise HTTPException(401, "Invalid or missing credentials.", headers={"WWW-Authenticate": "Bearer"})


router = APIRouter(prefix="/internal/audits", tags=["internal"], dependencies=[Depends(require_internal_token)])


@router.post("/execute/", status_code=202, response_model=AcceptedOut)
async def execute(
    request: Request,
    response: Response,
    payload: str = Form(...),
    documentation: UploadFile | None = File(default=None),
    runs: RunManager = Depends(get_runs),
):
    settings = request.app.state.settings
    try:
        req = AuditRequest.model_validate_json(payload)
    except ValidationError as e:
        raise HTTPException(422, [{"loc": [str(x) for x in err["loc"]], "msg": err["msg"]} for err in e.errors()]) from None

    data, ext = None, ""
    if documentation is not None and documentation.filename:
        ext = Path(documentation.filename).suffix.lower()  # the name itself is never used on disk
        if ext not in ALLOWED_DOC_EXT:
            raise HTTPException(400, "Unsupported documentation file type.")
        data = await documentation.read(settings.agent_max_doc_bytes + 1)
        if len(data) > settings.agent_max_doc_bytes:
            raise HTTPException(413, "Documentation file too large.")

    # No awaits below: lookup + submit is atomic with respect to other requests.
    existing = runs.lookup(req)
    if existing:
        response.status_code = 200
        return AcceptedOut(audit_id=existing.audit_id, state=existing.state)
    if runs.at_capacity():
        raise HTTPException(503, "Agent service is busy.")
    doc_path = None
    if data is not None:
        work = runs.work_dir_for(req)
        work.mkdir(parents=True, exist_ok=True)
        doc_path = work / f"documentation{ext}"
        doc_path.write_bytes(data)
    rec, _ = runs.submit(req, doc_path)
    return AcceptedOut(audit_id=rec.audit_id, state=rec.state)


@router.get("/{audit_id}/status/", response_model=StatusOut)
async def audit_status(audit_id: UUID, runs: RunManager = Depends(get_runs)):
    rec = runs.get(str(audit_id))
    if rec is None:
        raise HTTPException(404, "Unknown audit.")
    return rec.to_status()


@router.post("/{audit_id}/cancel/", response_model=AcceptedOut)
async def cancel_audit(audit_id: UUID, runs: RunManager = Depends(get_runs)):
    rec = runs.cancel(str(audit_id))
    if rec is None:
        raise HTTPException(404, "Unknown audit.")
    return AcceptedOut(audit_id=rec.audit_id, state=rec.state)