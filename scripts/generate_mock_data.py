import os
import random
from datetime import datetime, timedelta

import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(OUT, exist_ok=True)

random.seed(42)

skus = ["SKU-A", "SKU-B", "SKU-C", "SKU-D"]
platforms = ["meta", "google", "tiktok", "amazon"]
dates = [datetime(2024, 6, 1) + timedelta(days=i) for i in range(30)]

ads = []
for d in dates:
    for p in platforms:
        for s in skus:
            ads.append({
                "date": d.date(),
                "platform": p,
                "campaign_id": f"{p}_{s}_001",
                "sku": s,
                "spend": round(random.uniform(80, 600), 2),
                "impressions": random.randint(2000, 50000),
                "clicks": random.randint(50, 1500),
            })
pd.DataFrame(ads).to_csv(f"{OUT}/ad_spend.csv", index=False)

sales = []
for d in dates:
    for p in platforms:
        for s in skus:
            units = random.randint(0, 60)
            price = {"SKU-A": 40, "SKU-B": 60, "SKU-C": 25, "SKU-D": 90}[s]
            sales.append({
                "date": d.date(),
                "platform": p,
                "sku": s,
                "units_sold": units,
                "revenue": round(units * price * random.uniform(0.9, 1.05), 2),
            })
pd.DataFrame(sales).to_csv(f"{OUT}/sales.csv", index=False)

ga = []
for d in dates:
    for p in platforms:
        for s in skus:
            sess = random.randint(100, 3000)
            atc = int(sess * random.uniform(0.05, 0.2))
            pur = int(atc * random.uniform(0.2, 0.6))
            ga.append({
                "date": d.date(),
                "channel": p,
                "sku": s,
                "sessions": sess,
                "add_to_cart": atc,
                "purchases": pur,
            })
pd.DataFrame(ga).to_csv(f"{OUT}/ga_events.csv", index=False)

inv = [{"sku": s, "inventory_units": random.randint(0, 500)} for s in skus]
pd.DataFrame(inv).to_csv(f"{OUT}/inventory.csv", index=False)

margins = [{"sku": s, "margin_pct": round(random.uniform(0.15, 0.55), 3)}
           for s in skus]
pd.DataFrame(margins).to_csv(f"{OUT}/sku_margins.csv", index=False)

print("Mock data written to", OUT)
