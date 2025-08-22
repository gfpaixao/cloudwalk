import pandas as pd

# load your CSV
df = pd.read_csv("data/Operations_analyst_data.csv")

print("Rows, Cols:", df.shape)
print("\nColumns:", list(df.columns))
print("\nPreview:")
print(df.head(5).to_string(index=False))
