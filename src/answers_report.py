# src/answers_report.py
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path("data/Operations_analyst_data.csv")
OUT = Path("outputs"); OUT.mkdir(exist_ok=True)

# ---------- load & clean ----------
df = pd.read_csv(RAW, dtype=str)
num_cols = ["amount_transacted","quantity_transactions","installments"]
for c in num_cols:
    df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0)
df["day"] = pd.to_datetime(df["day"], errors="coerce")
df["month"] = df["day"].dt.to_period("M").astype(str)
df["weekday"] = df["day"].dt.day_name()

norm = lambda s: s.fillna("").str.strip().str.lower().str.replace(" ", "_")
df["entity"] = df["entity"].fillna("").str.strip()
df["product"] = norm(df["product"])
df["payment_method"] = norm(df["payment_method"])
df["anticipation_method"] = norm(df["anticipation_method"])

# fix: Pix/Bank slip rows should have same payment_method
mask = df["anticipation_method"].isin(["pix","bank_slip"])
df.loc[mask, "payment_method"] = df.loc[mask, "anticipation_method"]

# monthly tier buckets (from your rules)
def tier(v):
    if v <= 20000: return "0-20k"
    if v <= 40000: return "20k-40k"
    if v <= 80000: return "40k-80k"
    return "80k+"
df["monthly_tier"] = df["amount_transacted"].apply(tier)

# row avg ticket
df["avg_ticket_row"] = np.where(df["quantity_transactions"]>0,
                                df["amount_transacted"]/df["quantity_transactions"], 0.0)

# helper for printing
money = lambda v: f"R$ {v:,.2f}"
pct   = lambda v: f"{v*100:,.2f}%"

def agg_basic(g):
    amt = g["amount_transacted"].sum()
    tx  = g["quantity_transactions"].sum()
    return pd.Series({"tpv": amt, "transactions": tx, "avg_ticket": (amt/tx) if tx else 0.0})

# pre-aggregations reused below
by_epm = df.groupby(["entity","product","payment_method"], dropna=False).apply(agg_basic).reset_index()

lines = []

def section(title): 
    lines.append(f"\n## {title}")

# 0) decision hook
section("Decision hook")
total_tpv = df["amount_transacted"].sum()
lines.append(f"Total TPV: {money(total_tpv)}")

# 1) product preference by entity
section("Product preference by entity (TPV)")
tmp = by_epm.groupby(["entity","product"], as_index=False)["tpv"].sum()
for ent, sub in tmp.groupby("entity"):
    best = sub.sort_values("tpv", ascending=False).iloc[0]
    lines.append(f"{ent}: {best['product']} ({money(best['tpv'])})")

# 2) payment method preference by entity
section("Payment method preference by entity (TPV)")
pm = by_epm.groupby(["entity","payment_method"], as_index=False)["tpv"].sum()
for ent, sub in pm.groupby("entity"):
    best = sub.sort_values("tpv", ascending=False).iloc[0]
    lines.append(f"{ent}: {best['payment_method']} ({money(best['tpv'])})")

# 3) top product overall
section("Top product overall (TPV)")
prod = by_epm.groupby("product", as_index=False)["tpv"].sum().sort_values("tpv", ascending=False)
lines.append(f"{prod.iloc[0]['product']} ({money(prod.iloc[0]['tpv'])})")

# 4) top payment method overall + shares
section("Payment method mix (overall)")
pm_over = pm.groupby("payment_method", as_index=False)["tpv"].sum()
pm_over["share"] = pm_over["tpv"] / pm_over["tpv"].sum()
for _, r in pm_over.sort_values("tpv", ascending=False).iterrows():
    lines.append(f"{r['payment_method']}: {money(r['tpv'])} ({pct(r['share'])})")
lines.append(f"TOTAL TPV: {money(pm_over['tpv'].sum())}")

# 5) entity with biggest TPV + shares
section("Entity mix (overall)")
ent_over = by_epm.groupby("entity", as_index=False)["tpv"].sum()
ent_over["share"] = ent_over["tpv"]/ent_over["tpv"].sum()
for _, r in ent_over.sort_values("tpv", ascending=False).iterrows():
    lines.append(f"{r['entity']}: {money(r['tpv'])} ({pct(r['share'])})")

# 6–8) stats of amount_transacted by entity/product/payment_method
def stats_block(level, label):
    g = df.groupby(level)["amount_transacted"]
    s = (pd.DataFrame({
        "avg": g.mean(), "median": g.median(), "mode": g.apply(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan),
        "n": g.size()
    }).reset_index().sort_values("avg", ascending=False))
    section(f"Amount stats by {label} (avg/median/mode)")
    for _, r in s.iterrows():
        m = "—" if pd.isna(r['mode']) else money(r['mode'])
        lines.append(f"{r[level]}: avg {money(r['avg'])} · med {money(r['median'])} · mode {m} · n {int(r['n'])}")

stats_block("entity","entity")
stats_block("product","product")
stats_block("payment_method","payment method")

# 9–10) installments impact (credit only)
section("Installments impact (credit only)")
credit = df[df["payment_method"]=="credit"].copy()
inst = credit.groupby("installments").apply(agg_basic).reset_index()
inst["share_tpv"] = inst["tpv"]/inst["tpv"].sum()
for _, r in inst.sort_values("installments").iterrows():
    lines.append(f"{int(r['installments'])}x: TPV {money(r['tpv'])} ({pct(r['share_tpv'])}), avg_ticket {money(r['avg_ticket'])}")
best_inst = inst.sort_values("tpv", ascending=False).iloc[0]
lines.append(f"Top installment by TPV: {int(best_inst['installments'])}x ({money(best_inst['tpv'])})")

# 11–12) price tier biggest/lowest TPV
section("Price tier performance (TPV)")
tier = df.groupby("monthly_tier", as_index=False)["amount_transacted"].sum().rename(columns={"amount_transacted":"tpv"})
for _, r in tier.sort_values("tpv", ascending=False).iterrows():
    lines.append(f"{r['monthly_tier']}: {money(r['tpv'])}")
lines.append(f"Top tier: {tier.sort_values('tpv', ascending=False).iloc[0]['monthly_tier']}")
lines.append(f"Lowest tier: {tier.sort_values('tpv', ascending=True).iloc[0]['monthly_tier']}")

# 13–14) weekday effect
section("Weekday effect (TPV)")
wk = df.groupby("weekday", as_index=False)["amount_transacted"].sum().rename(columns={"amount_transacted":"tpv"})
wk["weekday"] = pd.Categorical(wk["weekday"], ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], ordered=True)
for _, r in wk.sort_values("weekday").iterrows():
    lines.append(f"{r['weekday']}: {money(r['tpv'])}")
lines.append(f"Top weekday: {wk.sort_values('tpv', ascending=False).iloc[0]['weekday']}")

# 15) time of year (month) with biggest TPV
section("Month with biggest TPV")
mo = df.groupby("month", as_index=False)["amount_transacted"].sum().rename(columns={"amount_transacted":"tpv"})
lines.append(f"Top month: {mo.sort_values('tpv', ascending=False).iloc[0]['month']} "
             f"({money(mo['tpv'].max())})")

# 16) anticipation method most used by each entity + avg ticket Nitro vs D1
section("Anticipation method by entity")
ant = (df.groupby(["entity", "anticipation_method"], as_index=False)
         .agg(transactions=("quantity_transactions", "sum"),
              tpv=("amount_transacted", "sum")))
ant["share"] = ant["tpv"] / ant.groupby("entity")["tpv"].transform("sum")
for ent, sub in ant.groupby("entity"):
    best = sub.sort_values("tpv", ascending=False).iloc[0]
    lines.append(f"{ent}: {best['anticipation_method']} ({money(best['tpv'])}, {pct(best['share'])})")

section("Avg ticket: D0/Nitro vs D1Anticipation (credit only)")
ant_ct = credit.groupby("anticipation_method").apply(agg_basic).reset_index()
for _, r in ant_ct.iterrows():
    lines.append(f"{r['anticipation_method']}: avg_ticket {money(r['avg_ticket'])} (TPV {money(r['tpv'])})")

# 17) which anticipation brings biggest TPV overall
section("Top anticipation method (overall TPV)")
ant_over = df.groupby("anticipation_method", as_index=False)["amount_transacted"].sum().rename(columns={"amount_transacted":"tpv"})
ant_over["share"] = ant_over["tpv"]/ant_over["tpv"].sum()
for _, r in ant_over.sort_values("tpv", ascending=False).iterrows():
    lines.append(f"{r['anticipation_method']}: {money(r['tpv'])} ({pct(r['share'])})")

# 18) best client type (top TPV combination)
section("Best client type by TPV (entity × product × payment × anticipation × tier × installments)")
combo = (df.groupby(["entity","product","payment_method","anticipation_method","monthly_tier","installments"], as_index=False)
           .agg(tpv=("amount_transacted","sum")))
topc = combo.sort_values("tpv", ascending=False).iloc[0]
lines.append(f"{topc.to_dict()}")

# 21) who drives TPV: big vs small average tickets (deciles of row avg_ticket)
section("TPV by avg_ticket deciles (row-level)")
dec = pd.qcut(df["avg_ticket_row"].replace([np.inf,-np.inf], np.nan).fillna(0), 10, labels=False, duplicates="drop")
df["ticket_decile"] = dec
by_dec = df.groupby("ticket_decile", as_index=False)["amount_transacted"].sum().rename(columns={"amount_transacted":"tpv"})
share = by_dec["tpv"]/by_dec["tpv"].sum()
for _, r in by_dec.assign(share=share).sort_values("ticket_decile").iterrows():
    lines.append(f"decile {int(r['ticket_decile'])+1}: TPV {money(r['tpv'])} ({pct(r['share'])})")
lines.append(f"Top decile: {int(by_dec.sort_values('tpv', ascending=False).iloc[0]['ticket_decile'])+1}")

# ---------- write & print ----------
report = "\n".join(lines)
print(report)
(OUT/"report_summary.txt").write_text(report, encoding="utf-8")
print("\nSaved: outputs/report_summary.txt")
