# src/q6_stats_by_entity.py
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
df = pd.read_csv(RAW, dtype={"entity": str})

# use row-level amount_transacted (no daily aggregation)
df["amount_transacted"] = pd.to_numeric(df["amount_transacted"], errors="coerce").fillna(0.0)

def first_mode(s: pd.Series):
    m = s.mode(dropna=True)
    return m.iloc[0] if not m.empty else np.nan

stats = (
    df.groupby("entity")["amount_transacted"]
      .agg(avg="mean", median="median", mode=first_mode, n="size")
      .reset_index()
)

# pretty print
fmt = {
    "avg":    lambda v: f"R$ {v:,.2f}",
    "median": lambda v: f"R$ {v:,.2f}",
    "mode":   lambda v: "—" if pd.isna(v) else f"R$ {v:,.2f}",
}
print("amount_transacted stats by entity (row-level):")
print(stats[["entity","avg","median","mode","n"]].to_string(index=False, formatters=fmt))

# save
Path("outputs").mkdir(exist_ok=True)
stats.to_csv("outputs/kpi_stats_amount_by_entity.csv", index=False)
print("\nSaved: outputs/kpi_stats_amount_by_entity.csv")
