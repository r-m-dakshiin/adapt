from fastapi import APIRouter

from app.database import fetch_recent_events
from app.learning.feedback import record_outcome
from app.schemas import FeedbackRequest

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/events")
def recent_events(limit: int = 100):
    return {"events": fetch_recent_events(limit=limit)}


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
