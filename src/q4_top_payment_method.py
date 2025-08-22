# src/q4_top_payment_method.py
import pandas as pd
from pathlib import Path

kpi = Path("outputs/kpi_tpv_avg_by_entity_product_method.csv")
df = pd.read_csv(kpi)

pm = df.groupby("payment_method", as_index=False)["tpv"].sum()

total = pm["tpv"].sum()
if total == 0:
    print("No TPV found.")
    raise SystemExit(0)

pm["share"] = pm["tpv"] / total
pm = pm.sort_values("tpv", ascending=False)

print("TPV by payment method (overall):")
print(pm.to_string(
    index=False,
    formatters={
        "tpv":   lambda v: f"R$ {v:,.2f}",
        "share": lambda v: f"{v*100:,.2f}%"
    }
))

print(f"\nTOTAL TPV: R$ {total:,.2f}")
top = pm.iloc[0]
print(f"Top payment method: {top['payment_method']} "
      f"(R$ {top['tpv']:,.2f}, {top['share']*100:,.2f}%)")
