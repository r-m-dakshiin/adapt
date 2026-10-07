import numpy as np
import pandas as pd


def infer_drivers(df, entity_id):
    if df.empty:
        return []

    parts = entity_id.split("|")
    platform = parts[0] if len(parts) > 0 else None
    sku = parts[1] if len(parts) > 1 else None

    sub = df[(df["platform"] == platform) & (df["sku"] == sku)].sort_values("date")
    if len(sub) < 4:
        return []

    target = sub["roas"].astype(float)
    candidates = ["cvr", "cpa", "inventory_units", "stockout_risk",
                  "margin_pct", "spend", "sessions"]

    drivers = []
    for c in candidates:
        if c not in sub.columns:
            continue
        series = pd.to_numeric(sub[c], errors="coerce").fillna(0).astype(float)
        if series.std() == 0 or target.std() == 0:
            continue
        corr = float(np.corrcoef(series.values, target.values)[0, 1])
        drivers.append({
            "driver": c,
            "correlation": corr,
            "abs_correlation": abs(corr),
            "direction": "inverse" if corr < 0 else "direct",
        })

    drivers.sort(key=lambda x: x["abs_correlation"], reverse=True)
    return drivers[:5]
