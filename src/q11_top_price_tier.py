# src/q11_top_price_tier.py
import pandas as pd
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
df = pd.read_csv(RAW, dtype=str)

# normalize + numeric
norm = lambda s: s.fillna("").str.strip().str.lower().str.replace(" ", "_")
df["price_tier"] = norm(df.get("price_tier", ""))
df["amount_transacted"]     = pd.to_numeric(df["amount_transacted"], errors="coerce").fillna(0.0)
df["quantity_transactions"] = pd.to_numeric(df["quantity_transactions"], errors="coerce").fillna(0)

# aggregate
tier = (df.groupby("price_tier", as_index=False)
          .agg(tpv=("amount_transacted","sum"),
               transactions=("quantity_transactions","sum")))

tier["avg_ticket"] = (tier["tpv"] / tier["transactions"]).where(tier["transactions"]>0, 0)
tier["share"] = tier["tpv"] / tier["tpv"].sum()

# pretty print
tier = tier.sort_values("tpv", ascending=False)
fmt_money = lambda v: f"R$ {v:,.2f}"
fmt_int   = lambda v: f"{int(v):,}"
fmt_pct   = lambda v: f"{v*100:,.2f}%"

print("TPV by price_tier:")
print(tier.to_string(index=False, formatters={
    "tpv": fmt_money, "transactions": fmt_int,
    "avg_ticket": fmt_money, "share": fmt_pct
}))

top = tier.iloc[0]
bot = tier.iloc[-1]
print(f"\nTop price_tier: {top['price_tier']} (TPV {fmt_money(top['tpv'])}, {fmt_pct(top['share'])})")
print(f"Lowest price_tier: {bot['price_tier']} (TPV {fmt_money(bot['tpv'])}, {fmt_pct(bot['share'])})")

# save
Path("outputs").mkdir(exist_ok=True)
tier.to_csv("outputs/kpi_price_tier_tpv.csv", index=False)
print("\nSaved: outputs/kpi_price_tier_tpv.csv")
