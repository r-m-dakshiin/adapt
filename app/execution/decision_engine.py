import logging
from datetime import datetime, timezone

from app.intelligence import anomaly, causal, scoring
from app.intelligence.llm_agent import reason

logger = logging.getLogger(__name__)

# In-process recommendation store — resets on restart
_recommendations: list[dict] = []
_rec_seq = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def store_recommendation(rec: dict) -> dict:
    global _rec_seq
    _rec_seq += 1
    row = {"id": _rec_seq, "created_at": _now(), "status": "pending", **rec}
    _recommendations.append(row)
    return row


def get_recommendations(status: str | None = None) -> list[dict]:
    if status:
        return [r for r in reversed(_recommendations) if r.get("status") == status]
    return list(reversed(_recommendations))


def set_recommendation_status(rec_id: int, status: str):
    for r in _recommendations:
        if r.get("id") == rec_id:
            r["status"] = status
            return


def diagnose(df):
    anomalies = anomaly.detect_anomalies(df, metric="roas")

    drivers_map = {}
    for a in anomalies[:5]:
        drivers_map[a["entity_id"]] = causal.infer_drivers(df, a["entity_id"])

    scored = scoring.score_opportunities(df)
    top_opps = scored.head(5)[
        ["platform", "sku", "conversion_probability",
         "opportunity_score", "margin_pct", "stockout_risk"]
    ].to_dict(orient="records")

    context = {
        "anomalies": anomalies[:5],
        "drivers": list(drivers_map.values())[0] if drivers_map else [],
        "top_opportunities": top_opps,
    }
    llm_out = reason(context)

    persisted = []
    for r in llm_out.get("recommendations", []):
        row = {
            "entity_type": r.get("entity_type", "sku_campaign"),
            "entity_id": r.get("entity_id", ""),
            "action": r.get("action", "hold"),
            "from_entity": r.get("from_entity"),
            "to_entity": r.get("to_entity"),
            "delta_budget": float(r.get("delta_budget", 0.0) or 0.0),
            "confidence": float(r.get("confidence", 0.0) or 0.0),
            "rationale": r.get("rationale", ""),
            "metadata": {"source": "llm"},
        }
        persisted.append(store_recommendation(row))

    return {
        "anomalies": anomalies,
        "drivers": context["drivers"],
        "narrative": llm_out.get("narrative", ""),
        "recommendations": persisted,
        "top_opportunities": top_opps,
    }
