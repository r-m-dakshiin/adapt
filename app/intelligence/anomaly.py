import numpy as np
import pandas as pd


def detect_anomalies(df, metric="roas",
                     group_keys=("platform", "sku"),
                     z_threshold=2.0, min_history=3):
    if df.empty:
        return []

    anomalies = []
    df = df.sort_values("date").copy()

    for keys, group in df.groupby(list(group_keys)):
        if len(group) < min_history:
            continue
        values = group[metric].astype(float).values
        rolling_mean = pd.Series(values).rolling(window=min_history, min_periods=2).mean()
        rolling_std = pd.Series(values).rolling(window=min_history, min_periods=2).std()

        baseline = rolling_mean.iloc[-1]
        std = rolling_std.iloc[-1]
        current = values[-1]

        if pd.isna(baseline) or pd.isna(std) or std == 0:
            continue

        z = (current - baseline) / std
        if abs(z) >= z_threshold:
            delta_pct = (current - baseline) / baseline * 100 if baseline else 0.0
            severity = "critical" if abs(z) >= 3.0 else "warning"
            anomalies.append({
                "entity_type": "sku_campaign",
                "entity_id": "|".join(map(str, keys)),
                "platform": keys[0] if keys else None,
                "metric": metric,
                "current": float(current),
                "baseline": float(baseline),
                "delta_pct": float(delta_pct),
                "z_score": float(z),
                "severity": severity,
            })

    anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
    return anomalies
