import pandas as pd
from pathlib import Path

kpi = Path("outputs/kpi_tpv_avg_by_entity_product_method.csv")
df = pd.read_csv(kpi)

# TPV by entity & product
gp = (df.groupby(["entity","product"], as_index=False)["tpv"]
        .sum()
        .sort_values(["entity","tpv"], ascending=[True, False]))

print("TPV by entity & product:")
for ent, sub in gp.groupby("entity"):
    print(f"\n{ent}:")
    print(sub[["product","tpv"]].to_string(index=False,
            formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))

# Top product per entity
tops = gp.loc[gp.groupby("entity")["tpv"].idxmax()].reset_index(drop=True)
print("\nTop product per entity:")
print(tops.to_string(index=False,
        formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))
