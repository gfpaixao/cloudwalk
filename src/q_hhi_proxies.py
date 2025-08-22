# src/q_hhi_proxies.py
import pandas as pd
from pathlib import Path

kpi = Path("outputs/kpi_tpv_avg_by_entity_product_method.csv")
df = pd.read_csv(kpi)

def hhi_from_shares(s):
    # s are shares that sum to 1 for a given entity
    return float((s**2).sum())

# ----- HHI of payment-method mix within each entity -----
pm = df.groupby(["entity","payment_method"], as_index=False)["tpv"].sum()
pm["entity_tpv"] = pm.groupby("entity")["tpv"].transform("sum")
pm["share"] = pm["tpv"] / pm["entity_tpv"]
hhi_pm = pm.groupby("entity")["share"].apply(hhi_from_shares).reset_index(name="hhi_payment_method")

# ----- HHI of product mix within each entity -----
prod = df.groupby(["entity","product"], as_index=False)["tpv"].sum()
prod["entity_tpv"] = prod.groupby("entity")["tpv"].transform("sum")
prod["share"] = prod["tpv"] / prod["entity_tpv"]
hhi_prod = prod.groupby("entity")["share"].apply(hhi_from_shares).reset_index(name="hhi_product")

# Combine
out = hhi_pm.merge(hhi_prod, on="entity")
print("HHI proxies (0=diversified, 1=fully concentrated) within each entity:")
print(out.to_string(index=False))

Path("outputs").mkdir(exist_ok=True)
out.to_csv("outputs/kpi_hhi_proxies_by_entity.csv", index=False)
print("\nSaved: outputs/kpi_hhi_proxies_by_entity.csv")
