from typing import Optional
from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    rows_ingested: int
    unified_rows: int
    duration_ms: float


class AnomalyItem(BaseModel):
    entity_type: str
    entity_id: str
    platform: Optional[str] = None
    metric: str
    current: float
    baseline: float
    delta_pct: float
    z_score: float
    severity: str


class DiagnoseResponse(BaseModel):
    anomalies: list[AnomalyItem]
    narrative: str
    drivers: list[dict]


class Recommendation(BaseModel):
    id: Optional[int] = None
    entity_type: str
    entity_id: str
    action: str
    from_entity: Optional[str] = None
    to_entity: Optional[str] = None
    delta_budget: float = 0.0
    confidence: float = 0.0
    rationale: str
    metadata: dict = Field(default_factory=dict)


class ExecuteRequest(BaseModel):
    recommendation_id: int
    dry_run: bool = False


class ExecuteResponse(BaseModel):
    success: bool
    platform: str
    request: dict
    response: dict
    message: str


class FeedbackRequest(BaseModel):
    execution_id: int
    metric: str
    pre_value: float
    post_value: float
    window_hours: int = 24
    notes: Optional[str] = None
