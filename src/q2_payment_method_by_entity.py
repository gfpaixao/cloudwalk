import pandas as pd
from pathlib import Path

kpi = Path("outputs/kpi_tpv_avg_by_entity_product_method.csv")
df = pd.read_csv(kpi)

# TPV by entity & payment method
pm = (df.groupby(["entity","payment_method"], as_index=False)["tpv"]
        .sum()
        .sort_values(["entity","tpv"], ascending=[True, False]))

print("TPV by entity & payment method:")
for ent, sub in pm.groupby("entity"):
    print(f"\n{ent}:")
    print(sub[["payment_method","tpv"]].to_string(index=False,
            formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))

# Top method per entity
tops = pm.loc[pm.groupby("entity")["tpv"].idxmax()].reset_index(drop=True)
print("\nTop payment method per entity:")
print(tops.to_string(index=False,
        formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))

# Overall (optional)
overall = (pm.groupby("payment_method", as_index=False)["tpv"].sum()
             .sort_values("tpv", ascending=False))
print("\nOverall by payment method:")
print(overall.to_string(index=False,
        formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))
