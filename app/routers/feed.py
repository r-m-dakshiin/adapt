from datetime import datetime, timezone
from fastapi import APIRouter

from app.learning.feedback import record_outcome, _feedback
from app.schemas import FeedbackRequest

router = APIRouter(prefix="/feed", tags=["feed"])

# In-process event log
_events: list[dict] = []
_ev_seq = 0


def log_event(kind: str, entity_id: str = "", severity: str = "info", payload: dict = {}):
    global _ev_seq
    _ev_seq += 1
    _events.append({
        "id": _ev_seq,
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "entity_id": entity_id,
        "severity": severity,
        "payload": payload,
    })


@router.get("/events")
def recent_events(limit: int = 100):
    return {"events": list(reversed(_events))[:limit]}


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    return record_outcome(
        execution_id=req.execution_id,
        metric=req.metric,
        pre_value=req.pre_value,
        post_value=req.post_value,
        window_hours=req.window_hours,
        notes=req.notes,
    )
