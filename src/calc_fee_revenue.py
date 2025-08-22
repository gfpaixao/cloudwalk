# src/calc_fee_revenue.py
# -----------------------------------------------------------
# Fee engine with hard-coded rules (no external fee file).
# - Handles Link (credit only; NO debit).
# - Ignores Pix / Bank slip (fee = 0).
# - Logs invalid Link+Debit rows.
# Reads:  data/Operations_analyst_data.csv
# Writes: outputs/*.csv
# -----------------------------------------------------------
import pandas as pd
from pathlib import Path

TX_PATH = Path("data/Operations_analyst_data.csv")
OUTDIR  = Path("outputs")
OUTDIR.mkdir(exist_ok=True)

# ------------------------
# Helper: tier by amount
# ------------------------
def tier_for_amount(v: float) -> str:
    if v <= 20000:  return "<=20000"
    if v <= 40000:  return "20001-40000"
    if v <= 80000:  return "40001-80000"
    return ">80000"

# ---------------------------------------------------------
# RULES (decimals; e.g., 0.0344 = 3.44%)
# ---------------------------------------------------------

# D0/Nitro for NON-LINK (POS/TAP) — same for all tiers
D0_NONLINK = {
    ("debit", 1): 0.0279,
    ("credit", 1): 0.0599, ("credit", 2): 0.1139, ("credit", 3): 0.1249,
    ("credit", 4): 0.1309, ("credit", 5): 0.1379, ("credit", 6): 0.1449,
    ("credit", 7): 0.1549, ("credit", 8): 0.1609, ("credit", 9): 0.1669,
    ("credit",10): 0.1739, ("credit",11): 0.1839, ("credit",12): 0.1879,
}

# LINK (credit only) — tier-agnostic
LINK_D1 = {  # D1Anticipation
    1: 0.0420,  2: 0.0609,  3: 0.0701,  4: 0.0791,  5: 0.0880,  6: 0.0967,
    7: 0.1259,  8: 0.1342,  9: 0.1425, 10: 0.1506, 11: 0.1587, 12: 0.1666,
}
LINK_D0 = {  # D0/Nitro
    1: 0.0549,  2: 0.1089,  3: 0.1199,  4: 0.1259,  5: 0.1329,  6: 0.1399,
    7: 0.1499,  8: 0.1559,  9: 0.1619, 10: 0.1689, 11: 0.1789, 12: 0.1829,
}
# NOTE: there is NO debit for Link. We will log and zero out any such rows.

# D1Anticipation for NON-LINK (POS/TAP) — tiered
D1_NONLINK = {
    "<=20000": {
        ("debit", 1): 0.0157,
        ("credit", 1): 0.0344, ("credit", 2): 0.0557, ("credit", 3): 0.0630,
        ("credit", 4): 0.0703, ("credit", 5): 0.0774, ("credit", 6): 0.0845,
        ("credit", 7): 0.0916, ("credit", 8): 0.0986, ("credit", 9): 0.1055,
        ("credit",10): 0.1123, ("credit",11): 0.1191, ("credit",12): 0.1257,
    },
    "20001-40000": {
        ("debit", 1): 0.0105,
        ("credit", 1): 0.0318, ("credit", 2): 0.0453, ("credit", 3): 0.0514,
        ("credit", 4): 0.0574, ("credit", 5): 0.0635, ("credit", 6): 0.0694,
        ("credit", 7): 0.0754, ("credit", 8): 0.0812, ("credit", 9): 0.0870,
        ("credit",10): 0.0927, ("credit",11): 0.0985, ("credit",12): 0.1041,
    },
    "40001-80000": {
        ("debit", 1): 0.0099,
        ("credit", 1): 0.0308, ("credit", 2): 0.0439, ("credit", 3): 0.0495,
        ("credit", 4): 0.0551, ("credit", 5): 0.0607, ("credit", 6): 0.0662,
        ("credit", 7): 0.0717, ("credit", 8): 0.0772, ("credit", 9): 0.0826,
        ("credit",10): 0.0879, ("credit",11): 0.0932, ("credit",12): 0.0985,
    },
    ">80000": {
        ("debit", 1): 0.0094,
        ("credit", 1): 0.0298, ("credit", 2): 0.0425, ("credit", 3): 0.0477,
        ("credit", 4): 0.0528, ("credit", 5): 0.0579, ("credit", 6): 0.0629,
        ("credit", 7): 0.0681, ("credit", 8): 0.0729, ("credit", 9): 0.0781,
        ("credit",10): 0.0829, ("credit",11): 0.0879, ("credit",12): 0.0928,
    },
}

# ------------------------
# Load & normalize transactions
# ------------------------
df = pd.read_csv(TX_PATH)

# normalize text values
df["payment_method"] = df["payment_method"].str.lower().str.strip()
df["product"] = df["product"].str.lower().str.strip()
df["anticipation_method"] = df["anticipation_method"].str.replace(" ", "", regex=False).str.strip()
df["installments"] = df["installments"].fillna(1).astype(int)
df["amount_transacted"] = df["amount_transacted"].astype(float)

# harmonize "bank slip" variants
df["payment_method"] = df["payment_method"].replace({
    "bank slip": "bank_slip",
    "bank_slip": "bank_slip"
})

# per-row tier by amount
df["monthly_tier"] = df["amount_transacted"].apply(tier_for_amount)

# ------------------------
# Compute fee rate per row
# ------------------------
def fee_rate_for_row(row) -> float:
    pm   = row["payment_method"]              # 'credit' | 'debit' | 'pix' | 'bank_slip'
    prod = row["product"]                     # 'pos' | 'tap' | 'link' | 'pix' | 'bank_slip'
    ant  = row["anticipation_method"]         # 'D1Anticipation' | 'D0/Nitro'
    inst = int(row["installments"])
    tier = row["monthly_tier"]

    # free methods
    if pm in ("pix","bank_slip") or prod in ("pix","bank_slip"):
        return 0.0

    # LINK: credit only; debit is invalid → handled separately (logged + zeroed)
    if prod == "link":
        if pm == "credit":
            return (LINK_D0 if ant == "D0/Nitro" else LINK_D1).get(inst, 0.0)
        else:
            return 0.0  # invalid combo; we log it below

    # NON-LINK (pos/tap)
    if ant == "D0/Nitro":
        # Nitro ignores tier
        key = (pm, 1 if pm == "debit" else inst)
        return D0_NONLINK.get(key, 0.0)
    else:
        # D1 uses tiered table
        table = D1_NONLINK.get(tier, {})
        key = (pm, 1 if pm == "debit" else inst)
        return table.get(key, 0.0)

# calculate rates/revenue
df["fee_rate"] = df.apply(fee_rate_for_row, axis=1)
df["fee_revenue"] = df["amount_transacted"] * df["fee_rate"]

# ------------------------
# Log invalid Link+Debit rows (if any)
# ------------------------
invalid_link_debit = df[(df["product"]=="link") & (df["payment_method"]=="debit")]
if len(invalid_link_debit):
    invalid_link_debit.to_csv(OUTDIR/"invalid_link_debit.csv", index=False)
    print(f"[INFO] Found {len(invalid_link_debit):,} Link+Debit rows. Logged to outputs/invalid_link_debit.csv (fee set to 0).")

# ------------------------
# Save detailed + summaries
# ------------------------
detail_cols = [
    "day","entity","product","payment_method","anticipation_method",
    "installments","monthly_tier","amount_transacted","fee_rate","fee_revenue"
]
df[detail_cols].to_csv(OUTDIR/"fee_revenue_detailed.csv", index=False)

total_fee = df["fee_revenue"].sum()
print(f"TOTAL FEE REVENUE: R$ {total_fee:,.2f}")

(df.groupby("payment_method", as_index=False)["fee_revenue"]
   .sum().sort_values("fee_revenue", ascending=False)
   .to_csv(OUTDIR/"fees_by_payment_method.csv", index=False))

(df.groupby("anticipation_method", as_index=False)["fee_revenue"]
   .sum().sort_values("fee_revenue", ascending=False)
   .to_csv(OUTDIR/"fees_by_anticipation.csv", index=False))

(df[df["payment_method"]=="credit"]
   .groupby("installments", as_index=False)["fee_revenue"]
   .sum().sort_values("installments")
   .to_csv(OUTDIR/"fees_by_installments.csv", index=False))

print("Saved outputs/: fee_revenue_detailed.csv, fees_by_payment_method.csv, fees_by_anticipation.csv, fees_by_installments.csv")
