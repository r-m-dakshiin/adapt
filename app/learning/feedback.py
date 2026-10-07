from app.database import insert_feedback, log_event


def record_outcome(execution_id, metric, pre_value, post_value,
                   window_hours=24, notes=None):
    uplift = 0.0
    if pre_value:
        uplift = (post_value - pre_value) / pre_value * 100
    row = {
        "execution_id": execution_id,
        "metric": metric,
        "pre_value": pre_value,
        "post_value": post_value,
        "uplift": uplift,
        "window_hours": window_hours,
        "notes": notes,
    }
    saved = insert_feedback(row)
    log_event(
        kind="feedback",
        entity_type="execution",
        entity_id=str(execution_id),
        payload=saved,
        severity="info",
    )
    return saved
