# src/q12_lowest_tier_analysis.py
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
OUT = Path("outputs"); OUT.mkdir(exist_ok=True)

# ---------- load & normalize ----------
df = pd.read_csv(RAW, dtype=str)
num = ["amount_transacted","quantity_transactions","installments","quantity_of_merchants"]
for c in num:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

df["day"] = pd.to_datetime(df["day"], errors="coerce")
df["weekday"] = df["day"].dt.day_name()

norm = lambda s: s.fillna("").str.strip().str.lower().str.replace(" ", "_")
df["price_tier"] = norm(df.get("price_tier", ""))
df["product"] = norm(df.get("product",""))
df["payment_method"] = norm(df.get("payment_method",""))
df["anticipation_method"] = norm(df.get("anticipation_method",""))

# Pix/Bank slip label fix
mask = df["anticipation_method"].isin(["pix","bank_slip"])
df.loc[mask, "payment_method"] = df.loc[mask, "anticipation_method"]

# ---------- identify lowest & top tiers ----------
tier_tpv = df.groupby("price_tier", as_index=False)["amount_transacted"].sum().rename(columns={"amount_transacted":"tpv"})
tier_tpv = tier_tpv.sort_values("tpv", ascending=True)
lowest_tier = tier_tpv.iloc[0]["price_tier"] if not tier_tpv.empty else ""
top_tier    = tier_tpv.iloc[-1]["price_tier"] if not tier_tpv.empty else ""
overall_tpv = df["amount_transacted"].sum()

print("TPV by price_tier (ascending):")
print(tier_tpv.to_string(index=False, formatters={"tpv": lambda v: f"R$ {v:,.2f}"}))
print(f"\nLowest tier: {lowest_tier or '—'}")
print(f"Top tier:    {top_tier or '—'}")
print(f"TOTAL TPV:   R$ {overall_tpv:,.2f}")

# ---------- slice data ----------
lo = df[df["price_tier"] == lowest_tier].copy()
hi = df[df["price_tier"] == top_tier].copy()

def kpis(x: pd.DataFrame):
    tpv = x["amount_transacted"].sum()
    tx  = x["quantity_transactions"].sum()
    mer = x["quantity_of_merchants"].sum() if "quantity_of_merchants" in x.columns else np.nan
    avg_ticket = (tpv/tx) if tx else 0.0
    return tpv, tx, mer, avg_ticket

lo_tpv, lo_tx, lo_mer, lo_avg = kpis(lo)
hi_tpv, hi_tx, hi_mer, hi_avg = kpis(hi)

# ---------- mixes ----------
def mix(df_, dim):
    g = (df_.groupby(dim, as_index=False)["amount_transacted"].sum()
           .rename(columns={"amount_transacted":"tpv"}))
    total = g["tpv"].sum()
    if total > 0:
        g["share"] = g["tpv"]/total
    else:
        g["share"] = 0.0
    return g.sort_values("share", ascending=False)

lo_pm   = mix(lo, "payment_method")
lo_prod = mix(lo, "product")
lo_ant  = mix(lo, "anticipation_method")
lo_inst = mix(lo[lo["payment_method"]=="credit"], "installments")
lo_wd   = mix(lo, "weekday")

hi_pm   = mix(hi, "payment_method")
hi_prod = mix(hi, "product")
hi_ant  = mix(hi, "anticipation_method")

# ---------- save tables ----------
def save(df_, name): df_.to_csv(OUT/f"q12_{name}.csv", index=False)

save(tier_tpv, "tpv_by_price_tier")
save(lo_pm,   f"{lowest_tier}_mix_payment_method")
save(lo_prod, f"{lowest_tier}_mix_product")
save(lo_ant,  f"{lowest_tier}_mix_anticipation")
if not lo_inst.empty: save(lo_inst, f"{lowest_tier}_mix_installments_credit")
save(lo_wd,   f"{lowest_tier}_mix_weekday")
save(hi_pm,   f"{top_tier}_mix_payment_method")
save(hi_prod, f"{top_tier}_mix_product")
save(hi_ant,  f"{top_tier}_mix_anticipation")

# ---------- simple rule-based hypotheses ----------
lines = []
money = lambda v: f"R$ {v:,.2f}"
pct   = lambda v: f"{v*100:,.1f}%"

lines.append(f"Lowest price_tier: {lowest_tier}")
lines.append(f"TPV {money(lo_tpv)} vs Top tier {top_tier} TPV {money(hi_tpv)}")
lines.append(f"Avg ticket {money(lo_avg)} (low) vs {money(hi_avg)} (top)")
if not np.isnan(lo_mer) and not np.isnan(hi_mer):
    lines.append(f"Merchants (sum of rows): {int(lo_mer)} vs {int(hi_mer)} (top)")

def top_share(g):
    return (g.iloc[0][g.columns[0]], float(g.iloc[0]["share"])) if not g.empty else ("—", 0.0)

pm_name, pm_share = top_share(lo_pm)
prod_name, prod_share = top_share(lo_prod)
ant_name, ant_share = top_share(lo_ant)

lines.append(f"Top mixes in lowest tier → payment_method: {pm_name} ({pct(pm_share)}), "
             f"product: {prod_name} ({pct(prod_share)}), anticipation: {ant_name} ({pct(ant_share)})")

# Heuristics
hyp = []
if lo_avg < 0.6 * hi_avg:
    hyp.append("Lower average ticket likely suppresses TPV; focus on basket-building and higher-ticket use cases.")
if not lo_inst.empty and (lo_inst.assign(inst=lambda s: s["installments"].astype(int))
                             .sort_values("inst").iloc[0]["share"] > 0.6):
    hyp.append("Installments skewed to 1x; enabling/promoting multi-installments could lift TPV.")
if not lo_pm.empty and (lo_pm.loc[lo_pm["payment_method"].isin(["pix","debit","bank_slip"]), "share"].sum() > 0.6):
    hyp.append("Mix concentrated in Pix/Debit/Slip; shift to Credit (esp. higher installments) may increase value.")
if not lo_prod.empty and (lo_prod.iloc[0]["product"] in ["pos","tap"] and lo_prod.iloc[0]["share"] > 0.8):
    hyp.append("Offline-heavy mix; test Link or online flows to capture larger remote tickets.")
if not lo_wd.empty and (lo_wd.loc[lo_wd["weekday"].isin(["Saturday","Sunday"]), "share"].sum() < 0.2):
    hyp.append("Weak weekend contribution; try weekend promos or categories with weekend demand.")

if not hyp:
    hyp.append("No dominant pattern; inspect category/merchant mix or seasonality for this tier.")

report = "\n".join(lines + ["\nHypotheses:"] + [f"- {h}" for h in hyp])
print("\n" + report)
(OUT/"q12_lowest_tier_hypotheses.txt").write_text(report, encoding="utf-8")
print("\nSaved:")
print(" - outputs/q12_lowest_tier_hypotheses.txt")
print(" - outputs/q12_*.csv (mix breakdowns)")
