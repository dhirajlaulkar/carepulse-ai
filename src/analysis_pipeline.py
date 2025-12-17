from src.data_loader import load_data, clean_text
from src.nlp_engine import extract_risk_features
import pandas as pd

def main():
    print("Loading data...")
    df = load_data()
    if df is None or df.empty:
        print("No data loaded.")
        return

    print("Analyzing conversations...")
    # Apply cleaning
    df['cleaned_text'] = df['conversation'].apply(clean_text)
    
    # Generate Patient IDs if missing
    if 'patient_id' not in df.columns:
        df['patient_id'] = [f"P{i+1:03d}" for i in range(len(df))]
    
    # Apply NLP extraction
    # We apply to the original text for sentiment/keywords to preserve context, 
    # but cleaning might help some keyword matching if we did regex. 
    # For now, let's pass original text to `extract_risk_features` as it handles lowercasing.
    
    results = df['conversation'].apply(extract_risk_features)
    
    # Unpack results
    df['Risk Category'] = results.apply(lambda x: x[0])
    df['Risk Score'] = results.apply(lambda x: x[1])
    df['Symptoms'] = results.apply(lambda x: x[2])
    
    # Display insights
    print("\nanalysis Complete.")
    print("Risk Distribution:")
    print(df['Risk Category'].value_counts())
    
    print("\nTop 5 High Risk Patients:")
    high_risk = df[df['Risk Category'] == 'High'].head(5)
    for idx, row in high_risk.iterrows():
        print(f"ID: {idx} | Risk: {row['Risk Score']} | Symptoms: {row['Symptoms']}")
        print(f"Text: {row['conversation'][:100]}...\n")
        
    # Save processed data for Dashboard
    df.to_csv('data/processed_patients.csv', index=False)
    print("Results saved to data/processed_patients.csv")

if __name__ == "__main__":
    main()
