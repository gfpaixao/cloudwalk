# src/q10_top_installment.py
import pandas as pd
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
df = pd.read_csv(RAW, dtype=str)

# normalize + numeric
norm = lambda s: s.fillna("").strip().lower().replace(" ", "_") if isinstance(s, str) else ""
df["payment_method"] = df["payment_method"].fillna("").str.strip().str.lower().str.replace(" ", "_")
df["entity"] = df["entity"].fillna("").str.strip()
df["installments"] = pd.to_numeric(df.get("installments", 1), errors="coerce").fillna(1).astype(int)
df["amount_transacted"] = pd.to_numeric(df["amount_transacted"], errors="coerce").fillna(0.0)

# credit only
credit = df[df["payment_method"] == "credit"].copy()

# Overall top installment by TPV
overall = (credit.groupby("installments", as_index=False)["amount_transacted"].sum()
                 .rename(columns={"amount_transacted":"tpv"})
                 .sort_values("tpv", ascending=False))
top_overall = overall.iloc[0]

print("Overall TPV by installments (credit only):")
print(overall.sort_values("installments").to_string(index=False,
       formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))
print(f"\nTop installment overall: {int(top_overall['installments'])}x "
      f"(TPV R$ {top_overall['tpv']:,.2f})")

# Per-entity top installment
by_ent = (credit.groupby(["entity","installments"], as_index=False)["amount_transacted"].sum()
                .rename(columns={"amount_transacted":"tpv"}))
tops_ent = by_ent.loc[by_ent.groupby("entity")["tpv"].idxmax()].reset_index(drop=True)

print("\nTop installment by entity:")
for _, r in tops_ent.iterrows():
    print(f"{r['entity']}: {int(r['installments'])}x (TPV R$ {r['tpv']:,.2f})")

# save
Path("outputs").mkdir(exist_ok=True)
overall.to_csv("outputs/kpi_installments_overall_credit.csv", index=False)
tops_ent.to_csv("outputs/kpi_top_installment_by_entity.csv", index=False)
print("\nSaved: outputs/kpi_installments_overall_credit.csv and outputs/kpi_top_installment_by_entity.csv")
