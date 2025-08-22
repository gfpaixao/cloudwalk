# src/build_looker_dataset.py
import pandas as pd
from pathlib import Path

src = Path("outputs/fee_revenue_detailed.csv")
out = Path("outputs/looker_dataset.csv")

df = pd.read_csv(src)

# Fix payment_method: if it's "uninformed", use anticipation_method instead
if "payment_method" in df.columns and "anticipation_method" in df.columns:
    mask = df["payment_method"] == "uninformed"
    df.loc[mask, "payment_method"] = df.loc[mask, "anticipation_method"]

# Ensure types
if "day" in df.columns:
    df["day"] = pd.to_datetime(df["day"], errors="coerce").dt.date
for c in ["installments"]:
    if c in df.columns:
        df[c] = df[c].fillna(1).astype(int)
for c in ["amount_transacted","fee_revenue","fee_rate"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

# Effective take rate (safely)
df["effective_fee_rate"] = (df["fee_revenue"] / df["amount_transacted"]).fillna(0.0).replace([float("inf")], 0.0)

# Keep just what we need
cols = ["day","entity","product","payment_method","anticipation_method",
        "installments","monthly_tier","amount_transacted","fee_revenue","effective_fee_rate"]
df[cols].to_csv(out, index=False)
print(f"Saved {out} with {len(df)} rows")
