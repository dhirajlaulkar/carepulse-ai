import pandas as pd

try:
    df = pd.read_csv('data/patients.csv')
    print("Columns:", df.columns.tolist())
    print("\nFirst 2 rows:")
    print(df.head(2))
    print("\nInfo:")
    print(df.info())
except Exception as e:
    print(f"Error reading CSV: {e}")
