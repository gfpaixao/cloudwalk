# src/q9_installments_impact.py
import pandas as pd
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
df = pd.read_csv(RAW, dtype=str)

# normalize
norm = lambda s: s.fillna("").str.strip().str.lower().str.replace(" ", "_")
df["payment_method"] = norm(df["payment_method"])
df["installments"]   = pd.to_numeric(df.get("installments", 1), errors="coerce").fillna(1).astype(int)
df["amount_transacted"]     = pd.to_numeric(df["amount_transacted"], errors="coerce").fillna(0.0)
df["quantity_transactions"] = pd.to_numeric(df["quantity_transactions"], errors="coerce").fillna(0)

# credit only
credit = df[df["payment_method"]=="credit"].copy()

# aggregate by installments
agg = (credit.groupby("installments", as_index=False)
              .agg(tpv=("amount_transacted","sum"),
                   transactions=("quantity_transactions","sum")))
agg["avg_ticket"] = (agg["tpv"] / agg["transactions"]).where(agg["transactions"]>0, 0)

# shares (impact)
agg["tpv_share"] = agg["tpv"] / agg["tpv"].sum()
agg["tx_share"]  = agg["transactions"] / agg["transactions"].sum()

# nice order & print
agg = agg.sort_values("installments")
fmt = {
    "tpv":        lambda v: f"R$ {v:,.2f}",
    "transactions": lambda v: f"{int(v):,}",
    "avg_ticket": lambda v: f"R$ {v:,.2f}",
    "tpv_share":  lambda v: f"{v*100:,.2f}%",
    "tx_share":   lambda v: f"{v*100:,.2f}%",
}
print("Installments impact (credit only):")
print(agg.to_string(index=False, formatters=fmt))

top = agg.sort_values("tpv", ascending=False).iloc[0]
print(f"\nTop installment by TPV: {int(top['installments'])}x "
      f"(TPV {fmt['tpv'](top['tpv'])}, share {fmt['tpv_share'](top['tpv_share'])})")

# save
Path("outputs").mkdir(exist_ok=True)
agg.to_csv("outputs/kpi_installments_impact_credit.csv", index=False)
print("\nSaved: outputs/kpi_installments_impact_credit.csv")
