# src/viz_outputs.py
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (9, 5),
    "axes.grid": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

def _num(x):
    """coerce to numeric safely"""
    return pd.to_numeric(x, errors="coerce")

def _save(fig, name):
    fig.tight_layout()
    p = FIG / f"{name}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(f"✓ saved {p.relative_to(ROOT)}")

# 1) TPV by weekday
def plot_weekday():
    p = OUT / "kpi_weekday.csv"
    if not p.exists(): return
    df = pd.read_csv(p)
    cols = {c.lower(): c for c in df.columns}
    wk = df.rename(columns=cols)
    # try to order Mon..Sun if present; fall back to current order
    order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    key = next((c for c in ["weekday","day_name","week_day"] if c in wk.columns), None)
    val = next((c for c in ["tpv","amount_transacted","value"] if c in wk.columns), None)
    if key is None or val is None: return
    wk[val] = _num(wk[val])
    try:
        wk["_ord"] = wk[key].str[:3].str.title().map({k:i for i,k in enumerate(order)})
        wk = wk.sort_values("_ord")
    except Exception:
        pass
    fig, ax = plt.subplots()
    ax.bar(wk[key], wk[val])
    ax.set_title("TPV by weekday")
    ax.set_ylabel("TPV")
    _save(fig, "weekday_tpv")

# 2) Credit installments impact
def plot_installments_credit():
    p = OUT / "kpi_installments_credit.csv"
    if not p.exists(): return
    df = pd.read_csv(p)
    cols = {c.lower(): c for c in df.columns}
    ins = df.rename(columns=cols)
    if "installments" not in ins.columns: return
    y_col = next((c for c in ["tpv","fee_revenue","amount_transacted"] if c in ins.columns), None)
    if y_col is None: return
    ins["installments"] = _num(ins["installments"])
    ins[y_col] = _num(ins[y_col])
    ins = ins.sort_values("installments")
    fig, ax = plt.subplots()
    ax.bar(ins["installments"].astype(int), ins[y_col])
    ax.set_title(f"{y_col.replace('_',' ').title()} by credit installments")
    ax.set_xlabel("installments")
    ax.set_ylabel(y_col.replace('_',' ').title())
    _save(fig, "installments_credit")

# 3) Amount percentiles by entity (P50–P99)
def plot_percentiles_by_entity():
    p = OUT / "kpi_percentiles_amount_by_entity.csv"
    if not p.exists(): return
    df = pd.read_csv(p)
    cols = {c.lower(): c for c in df.columns}
    d = df.rename(columns=cols)
    if "entity" not in d.columns: return
    perc_cols = [c for c in d.columns if c.lower().startswith("p")]
    if not perc_cols: return
    for c in perc_cols: d[c] = _num(d[c])
    m = d.set_index("entity")[perc_cols].T  # rows: percentiles
    fig, ax = plt.subplots()
    for ent in m.columns:
        ax.plot(m.index, m[ent], marker="o", label=ent)
    ax.set_title("Amount transacted percentiles by entity")
    ax.set_xlabel("percentile")
    ax.set_ylabel("Amount")
    ax.legend(title="entity")
    _save(fig, "amount_percentiles_by_entity")

# 4) Price tier – TPV and Transactions (if available)
def plot_price_tiers():
    p = OUT / "kpi_price_tier.csv"
    if not p.exists(): return
    df = pd.read_csv(p)
    cols = {c.lower(): c for c in df.columns}
    d = df.rename(columns=cols)
    if "price_tier" not in d.columns: return
    y = [c for c in ["tpv","transactions"] if c in d.columns]
    d[y] = d[y].apply(_num)
    d = d.sort_values("price_tier")
    fig, ax = plt.subplots()
    ax.bar(d["price_tier"], d[y[0]], label=y[0].title())
    if len(y) > 1:
        ax2 = ax.twinx()
        ax2.plot(d["price_tier"], d[y[1]], marker="o", color="tab:orange", label=y[1].title())
        ax2.set_ylabel(y[1].title())
        lines, labels = ax.get_legend_handles_labels()
        l2, lab2 = ax2.get_legend_handles_labels()
        ax.legend(lines + l2, labels + lab2, loc="upper left")
    ax.set_title("Price tier performance")
    ax.set_ylabel(y[0].title())
    _save(fig, "price_tier_perf")

# 5) Fees by payment method – bar + take rate
def plot_fees_by_payment_method():
    p = OUT / "fees_by_payment_method.csv"
    if not p.exists(): return
    df = pd.read_csv(p)
    cols = {c.lower(): c for c in df.columns}
    d = df.rename(columns=cols)
    if "payment_method" not in d.columns: return
    y_fee = next((c for c in ["fee_revenue","fees"] if c in d.columns), None)
    y_tpv = next((c for c in ["tpv","amount_transacted"] if c in d.columns), None)
    y_take = next((c for c in ["take_rate","take_rate_%","take_rate_pct"] if c in d.columns), None)
    for c in [y_fee, y_tpv, y_take]:
        if c: d[c] = _num(d[c])
    d = d.sort_values(y_fee or y_tpv, ascending=False)
    fig, ax = plt.subplots()
    ax.bar(d["payment_method"], d[y_fee or y_tpv], label=(y_fee or y_tpv).title())
    ax.set_ylabel((y_fee or y_tpv).title())
    if y_take:
        ax2 = ax.twinx()
        ax2.plot(d["payment_method"], d[y_take]* (100 if d[y_take].max() <= 1 else 1),
                 color="tab:orange", marker="o", label="Take Rate %")
        ax2.set_ylabel("Take Rate %")
        lines, labels = ax.get_legend_handles_labels()
        l2, lab2 = ax2.get_legend_handles_labels()
        ax.legend(lines + l2, labels + lab2, loc="upper right")
    ax.set_title("Fees by payment method")
    _save(fig, "fees_by_payment_method")

# 6) Entity × payment method – TPV heatmap (if mix file exists)
def plot_mix_heatmap():
    p = OUT / "kpi_mix_entity_x_payment_method.csv"
    if not p.exists(): return
    df = pd.read_csv(p)
    cols = {c.lower(): c for c in df.columns}
    d = df.rename(columns=cols)
    if not {"entity","payment_method"}.issubset(d.columns): return
    vcol = next((c for c in ["tpv_share","tpv","amount_transacted","share"] if c in d.columns), None)
    if vcol is None: return
    d[vcol] = _num(d[vcol])
    pivot = d.pivot_table(index="entity", columns="payment_method", values=vcol, aggfunc="sum")
    fig, ax = plt.subplots(figsize=(9, 4 + 0.3*pivot.shape[0]))
    im = ax.imshow(pivot.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(pivot.shape[1]), pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(pivot.shape[0]), pivot.index)
    ax.set_title(f"Entity × payment method ({vcol})")
    fig.colorbar(im, ax=ax, label=vcol)
    _save(fig, "mix_entity_payment_method")

def main():
    print("Building figures into outputs/figures/ ...")
    plot_weekday()
    plot_installments_credit()
    plot_percentiles_by_entity()
    plot_price_tiers()
    plot_fees_by_payment_method()
    plot_mix_heatmap()
    print("Done.")

if __name__ == "__main__":
    main()
