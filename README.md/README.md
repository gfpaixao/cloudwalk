# CloudWalk — Payments Insights (Operations Intelligence Analyst Challenge)

This repo contains a reproducible pipeline to analyze CloudWalk transactions and build the datasets used for a KPI dashboard (Looker Studio) and fee-revenue analysis.

## 🔧 What’s here

- **Data pipeline (Python)**
  - `src/calc_fee_revenue.py`  
    Applies business rules (installments, anticipation, product rules incl. Link credit-only) to compute `fee_rate` and `fee_revenue` per row.
  - `src/build_looker_dataset.py`  
    Produces a tidy dataset for BI: `outputs/looker_dataset.csv` with dates, segments, TPV, fee revenue, and effective take rate.
  - *(next step we’ll add)* `src/build_kpis.py`  
    Precomputes tables for the challenge KPIs (TPV, Avg Ticket, Installments, Price Tier, Weekday).

- **Dashboard (optional local)**
  - `src/app.py` (Streamlit) for quick local exploration.

- **Docs**
  - This README (context, KPI definitions, methods, and automation plan).

## 📦 How to run (local)

```bash
python -m pip install -r requirements.txt
# 1) Compute fees and detailed rows
python src/calc_fee_revenue.py
# 2) Build tidy BI dataset
python src/build_looker_dataset.py
# 3) (optional) Local dashboard
python -m streamlit run src/app.py
