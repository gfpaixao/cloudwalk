# src/q8_1_stats_by_price_tier.py
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
df = pd.read_csv(RAW, dtype=str)

# normalize + numeric
df["price_tier"] = (
    df.get("price_tier", "")
      .fillna("")
      .str.strip().str.lower().str.replace(" ", "_")
)
df["amount_transacted"] = pd.to_numeric(df["amount_transacted"], errors="coerce").fillna(0.0)

def first_mode(s: pd.Series):
    m = s.mode(dropna=True)
    return m.iloc[0] if not m.empty else np.nan

stats = (
    df.groupby("price_tier")["amount_transacted"]
      .agg(avg="mean", median="median", mode=first_mode, n="size")
      .reset_index()
      .sort_values("avg", ascending=False)
)

# pretty print
fmt = {
    "avg":    lambda v: f"R$ {v:,.2f}",
    "median": lambda v: f"R$ {v:,.2f}",
    "mode":   lambda v: "—" if pd.isna(v) else f"R$ {v:,.2f}",
}
print("amount_transacted stats by price_tier (row-level):")
print(stats[["price_tier","avg","median","mode","n"]].to_string(index=False, formatters=fmt))

# save
Path("outputs").mkdir(exist_ok=True)
out = Path("outputs/kpi_stats_amount_by_price_tier.csv")
stats.to_csv(out, index=False)
print(f"\nSaved: {out}")
