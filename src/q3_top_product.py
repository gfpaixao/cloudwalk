import pandas as pd
from pathlib import Path

kpi_path = Path("outputs/kpi_tpv_avg_by_entity_product_method.csv")
df = pd.read_csv(kpi_path)

# TPV by product (overall)
prod = (df.groupby("product", as_index=False)["tpv"]
          .sum()
          .sort_values("tpv", ascending=False))

print("TPV by product (overall):")
print(prod.to_string(index=False, formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))

top = prod.iloc[0]
print(f"\nTop product by TPV: {top['product']}  (R$ {top['tpv']:,.2f})")

# (bonus) TPV by entity & product
by_ent = (df.groupby(["entity","product"], as_index=False)["tpv"]
            .sum()
            .sort_values(["entity","tpv"], ascending=[True, False]))

print("\nTPV by entity & product:")
for ent, sub in by_ent.groupby("entity"):
    print(f"\n{ent}:")
    print(sub[["product","tpv"]].to_string(index=False,
                                           formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))
