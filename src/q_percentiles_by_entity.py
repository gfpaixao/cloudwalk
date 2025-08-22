# src/q_percentiles_by_entity.py
import pandas as pd
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
df = pd.read_csv(RAW, dtype={"entity": str})

# numeric
df["amount_transacted"] = pd.to_numeric(df["amount_transacted"], errors="coerce").fillna(0.0)

# percentiles by entity (row-level amounts)
q = (df.groupby("entity")["amount_transacted"]
       .quantile([0.50, 0.75, 0.90, 0.95, 0.99])
       .unstack())  # columns are the probs

q.columns = ["p50","p75","p90","p95","p99"]
q = q.reset_index()

# pretty print
fmt = {c: (lambda v: f"R$ {v:,.2f}") for c in ["p50","p75","p90","p95","p99"]}
print("Row-level amount_transacted percentiles by entity:")
print(q.to_string(index=False, formatters=fmt))

# save
Path("outputs").mkdir(exist_ok=True)
out = Path("outputs/kpi_percentiles_amount_by_entity.csv")
q.to_csv(out, index=False)
print(f"\nSaved: {out}")
