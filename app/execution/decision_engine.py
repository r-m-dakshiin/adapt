import logging

from app.database import insert_recommendation
from app.intelligence import anomaly, causal, scoring
from app.intelligence.llm_agent import reason

logger = logging.getLogger(__name__)


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
        saved = insert_recommendation(row)
        persisted.append(saved or row)

    return {
        "anomalies": anomalies,
        "drivers": context["drivers"],
        "narrative": llm_out.get("narrative", ""),
        "recommendations": persisted,
        "top_opportunities": top_opps,
    }
