# src/build_kpis.py
import pandas as pd
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
OUT = Path("outputs"); OUT.mkdir(exist_ok=True)

df = pd.read_csv(RAW, dtype=str)
# types
num = ["amount_transacted","quantity_transactions","installments"]
for c in num:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# dates & labels
df["day"] = pd.to_datetime(df["day"], errors="coerce")
df["weekday"] = df["day"].dt.day_name()
df["payment_method"] = df["payment_method"].str.strip().str.lower().str.replace(" ", "_")
df["anticipation_method"] = df["anticipation_method"].str.strip().str.lower().str.replace(" ", "_")
df["product"] = df["product"].str.strip().str.lower()
df["entity"] = df["entity"].str.strip()

# fix uninformed: make payment_method = anticipation_method for pix/bank_slip
mask = df["anticipation_method"].isin(["pix","bank_slip"])
df.loc[mask, "payment_method"] = df.loc[mask, "anticipation_method"]

# helpers
def agg_basic(g):
    amt = g["amount_transacted"].sum()
    tx  = g["quantity_transactions"].sum()
    return pd.Series({
        "tpv": amt,
        "transactions": tx,
        "avg_ticket": (amt/tx) if tx else 0.0
    })

# 1) TPV & Avg Ticket by entity, product, payment_method
kpi1 = df.groupby(["entity","product","payment_method"], dropna=False).apply(agg_basic).reset_index()
kpi1.to_csv(OUT/"kpi_tpv_avg_by_entity_product_method.csv", index=False)

# 2) Installments analysis (credit only)
credit = df[df["payment_method"]=="credit"].copy()
kpi2 = credit.groupby(["installments"], dropna=False).apply(agg_basic).reset_index().sort_values("installments")
kpi2.to_csv(OUT/"kpi_installments_credit.csv", index=False)

# 3) Price tier analysis (use provided 'price_tier')
tier_col = "price_tier" if "price_tier" in df.columns else None
if tier_col:
    kpi3 = df.groupby([tier_col], dropna=False).apply(agg_basic).reset_index().rename(columns={tier_col:"price_tier"})
    kpi3.to_csv(OUT/"kpi_price_tier.csv", index=False)

# 4) Weekday effect
weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
kpi4 = df.groupby(["weekday"], dropna=False).apply(agg_basic).reset_index()
kpi4["weekday"] = pd.Categorical(kpi4["weekday"], categories=weekday_order, ordered=True)
kpi4 = kpi4.sort_values("weekday")
kpi4.to_csv(OUT/"kpi_weekday.csv", index=False)

# 5) Anticipation usage by entity
kpi5 = df.groupby(["entity","anticipation_method"], dropna=False).apply(agg_basic).reset_index()
kpi5.to_csv(OUT/"kpi_anticipation_by_entity.csv", index=False)

print("Saved:", [
    "kpi_tpv_avg_by_entity_product_method.csv",
    "kpi_installments_credit.csv",
    "kpi_price_tier.csv" if tier_col else "(no price_tier in data)",
    "kpi_weekday.csv",
    "kpi_anticipation_by_entity.csv",
])
