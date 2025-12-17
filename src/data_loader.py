import pandas as pd
import numpy as np
import re

def load_data(filepath='data/patients.csv'):
    """
    Loads the patient conversation data from a CSV file.
    Handles potential parsing errors.
    """
    try:
        # Try reading with default settings first, but ready to handle bad lines
        df = pd.read_csv(filepath, on_bad_lines='skip', engine='python')
        print(f"Successfully loaded {len(df)} rows.")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def clean_text(text):
    """
    Basic text cleaning:
    - Lowercase
    - Remove special characters
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

if __name__ == "__main__":
    df = load_data()
    if df is not None:
        print("Columns:", df.columns.tolist())
        if 'conversation' in df.columns:
            df['cleaned_text'] = df['conversation'].apply(clean_text)
            print("First 5 cleaned rows:")
            print(df[['conversation', 'cleaned_text']].head())
        else:
            print("Row 'conversation' not found. Available columns:", df.columns)
