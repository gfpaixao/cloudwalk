# src/fix_payment_method.py
import pandas as pd
from pathlib import Path
import shutil

OPS = Path("data/Operations_analyst_data.csv")

# safety backup (one time per run)
backup = OPS.with_name(OPS.stem + "_backup.csv")
shutil.copyfile(OPS, backup)

# load as text so we don't lose any formatting
df = pd.read_csv(OPS, dtype=str)

# normalize strings
df["anticipation_method"] = df["anticipation_method"].fillna("").str.strip()
df["payment_method"] = df["payment_method"].fillna("").str.strip()

# rows where anticipation is Pix or Bank Slip (any spelling)
a_lower = df["anticipation_method"].str.lower()
mask = a_lower.isin(["pix","bank slip","bankslip","bank_slip"])

# canonicalize the value we will write back
def canon(x: str) -> str:
    s = str(x).strip().lower()
    if s == "pix":
        return "Pix"
    if s in ["bank slip","bankslip","bank_slip","bank  slip"]:
        return "Bank slip"
    return x  # fallback

df.loc[mask, "payment_method"] = df.loc[mask, "anticipation_method"].apply(canon)

print(f"Updated rows: {int(mask.sum())}")
df.to_csv(OPS, index=False)
print(f"Saved fixed file: {OPS}")
print(f"Backup kept at:  {backup}")
