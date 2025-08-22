# src/app.py
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Fee Revenue Dashboard", layout="wide")

detail_path = Path("outputs/fee_revenue_detailed.csv")
tx_path = Path("data/Operations_analyst_data.csv")

# --- Load data (expect you've already run src/calc_fee_revenue.py) ---
if not detail_path.exists():
    st.error("Run:  python src/calc_fee_revenue.py  first to generate outputs/fee_revenue_detailed.csv")
    st.stop()

df = pd.read_csv(detail_path)
# make sure dates behave
if "day" in df.columns:
    df["day"] = pd.to_datetime(df["day"], errors="coerce")

# --- Sidebar filters ---
st.sidebar.header("Filters")
products = sorted([p for p in df["product"].dropna().unique()])
p_methods = sorted([m for m in df["payment_method"].dropna().unique()])
anticips = sorted([a for a in df["anticipation_method"].dropna().unique()])
inst_min, inst_max = int(df["installments"].min()), int(df["installments"].max())

f_products = st.sidebar.multiselect("Product", products, default=products)
f_methods  = st.sidebar.multiselect("Payment method", p_methods, default=p_methods)
f_ants     = st.sidebar.multiselect("Anticipation", anticips, default=anticips)
f_inst     = st.sidebar.slider("Installments (credit)", inst_min, inst_max, (inst_min, inst_max))

# Apply filters
f = df.copy()
f = f[f["product"].isin(f_products)]
f = f[f["payment_method"].isin(f_methods)]
f = f[f["anticipation_method"].isin(f_ants)]
f = f[(f["installments"] >= f_inst[0]) & (f["installments"] <= f_inst[1])]

# --- KPIs ---
tpv = float(f["amount_transacted"].sum())
fee = float(f["fee_revenue"].sum())
take_rate = fee / tpv if tpv else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("TPV (filtered)", f"R$ {tpv:,.2f}")
c2.metric("Fee revenue", f"R$ {fee:,.2f}")
c3.metric("Effective fee rate", f"{take_rate*100:,.2f}%")

st.divider()

# --- Charts ---
col1, col2 = st.columns(2)

# Fee by payment method
pm = f.groupby("payment_method", as_index=False)["fee_revenue"].sum().sort_values("fee_revenue", ascending=False)
col1.plotly_chart(px.bar(pm, x="payment_method", y="fee_revenue",
                         title="Fee revenue by payment method"), use_container_width=True)

# Fee by anticipation
ant = f.groupby("anticipation_method", as_index=False)["fee_revenue"].sum().sort_values("fee_revenue", ascending=False)
col2.plotly_chart(px.bar(ant, x="anticipation_method", y="fee_revenue",
                         title="Fee revenue by anticipation"), use_container_width=True)

# Fee by installments (credit only)
cred = f[f["payment_method"] == "credit"]
if not cred.empty:
    inst = cred.groupby("installments", as_index=False)["fee_revenue"].sum().sort_values("installments")
    st.plotly_chart(px.line(inst, x="installments", y="fee_revenue",
                            markers=True, title="Fee revenue by installments (credit)"),
                    use_container_width=True)

# Fee over time
if "day" in f.columns and f["day"].notna().any():
    ts = f.groupby("day", as_index=False)["fee_revenue"].sum().sort_values("day")
    st.plotly_chart(px.line(ts, x="day", y="fee_revenue",
                            markers=True, title="Fee revenue over time"),
                    use_container_width=True)

# Fee by product
prod = f.groupby("product", as_index=False)["fee_revenue"].sum().sort_values("fee_revenue", ascending=False)
st.plotly_chart(px.bar(prod, x="product", y="fee_revenue",
                       title="Fee revenue by product"),
                use_container_width=True)

# --- Downloads ---
st.download_button("Download detailed CSV", data=df.to_csv(index=False).encode("utf-8"),
                   file_name="fee_revenue_detailed.csv", mime="text/csv")
