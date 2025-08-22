import pandas as pd

tx_path   = "data/Operations_analyst_data.csv"
fees_path = "fees/InfinitePay Fees.csv"   # rename here if your file name differs

# read transactions
tx = pd.read_csv(tx_path)
print("TRANSACTIONS  → rows, cols:", tx.shape)
print("tx columns:", list(tx.columns))
print("\nTx preview:")
print(tx.head(5).to_string(index=False))

# read fees (Portuguese Excel CSVs often = latin-1 + semicolon ;)
fees = pd.read_csv(fees_path, dtype=str, sep=';', encoding='latin-1')
print("\nFEES          → rows, cols:", fees.shape)
print("fees columns:", list(fees.columns))
print("\nFees preview:")
print(fees.head(10).to_string(index=False))

