import pandas as pd

df = pd.read_csv("data/health_dataset.csv")
print(df.head())
print("\nColumns:")
print(df.columns.tolist())