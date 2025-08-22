import pandas as pd
from pathlib import Path

kpi = Path("outputs/kpi_tpv_avg_by_entity_product_method.csv")
df = pd.read_csv(kpi)

ent = df.groupby("entity", as_index=False)["tpv"].sum()
total = ent["tpv"].sum()
ent["share"] = ent["tpv"] / total if total else 0
ent = ent.sort_values("tpv", ascending=False)

print("TPV by entity (overall):")
print(ent.to_string(
    index=False,
    formatters={
        "tpv":   lambda v: f"R$ {v:,.2f}",
        "share": lambda v: f"{v*100:,.2f}%"
    }
))

print(f"\nTOTAL TPV: R$ {total:,.2f}")
top = ent.iloc[0]
print(f"Top entity: {top['entity']} (R$ {top['tpv']:,.2f}, {top['share']*100:,.2f}%)")
