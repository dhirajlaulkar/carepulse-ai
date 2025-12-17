import pandas as pd
from textblob import TextBlob
import re

# Simple list of high-risk keywords/symptoms
HIGH_RISK_SYMPTOMS = [
    'chest pain', 'shortness of breath', 'difficulty breathing', 'suicide', 
    'suicidal', 'heart attack', 'stroke', 'seizure', 'unconscious', 
    'bleeding', 'severe pain', 'crushing', 'blue lips'
]

MEDIUM_RISK_SYMPTOMS = [
    'fever', 'migraine', 'vomiting', 'diarrhea', 'infection', 
    'cut', 'injury', 'dizzy', 'asthma', 'wheezing'
]

def get_sentiment_score(text):
    """
    Returns a sentiment polarity score between -1.0 (negative) and 1.0 (positive).
    """
    if not isinstance(text, str):
        return 0.0
    return TextBlob(text).sentiment.polarity

def extract_risk_features(text):
    """
    Analyzes text for symptoms and returns a risk category and score.
    """
    if not isinstance(text, str):
        return "Low", 0.0, []

    text_lower = text.lower()
    found_symptoms = []
    
    risk_score = 0.0
    
    # Check for High Risk
    for symptom in HIGH_RISK_SYMPTOMS:
        if symptom in text_lower:
            found_symptoms.append(symptom)
            risk_score += 10.0
            
    # Check for Medium Risk
    for symptom in MEDIUM_RISK_SYMPTOMS:
        if symptom in text_lower:
            found_symptoms.append(symptom)
            risk_score += 5.0
            
    sentiment = get_sentiment_score(text)
    
    # Adjust risk based on sentiment (Lower sentiment -> Higher risk slightly)
    if sentiment < -0.5:
        risk_score += 2.0
    elif sentiment < 0:
        risk_score += 1.0
        
    # Determine Category
    if risk_score >= 10.0:
        category = "High"
    elif risk_score >= 5.0:
        category = "Medium"
    else:
        category = "Low"
        
    return category, risk_score, found_symptoms

if __name__ == "__main__":
    # Test
    sample_texts = [
        "I have severe chest pain and cannot breathe.",
        "Just a mild headache.",
        "I feel very sad and hopeless.",
        "Scheduled checkup, feeling great."
    ]
    for text in sample_texts:
        cat, score, sx = extract_risk_features(text)
        print(f"Text: {text}\nRisk: {cat} (Score: {score}), Symptoms: {sx}\n")
