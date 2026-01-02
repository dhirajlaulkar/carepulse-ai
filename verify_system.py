from fastapi.testclient import TestClient
from app.main import app
from src.nlp_engine import extract_risk_features
from src.calendar_service import calendar_service
import pandas as pd
import os

client = TestClient(app)

def test_nlp():
    print("Testing NLP Engine...")
    text = "I have severe chest pain and cannot breathe."
    cat, score, symptoms = extract_risk_features(text)
    assert cat == "High"
    assert "chest pain" in symptoms
    print(" NLP Engine Passed")

def test_calendar():
    print("Testing Calendar Service...")
    appt = calendar_service.schedule_appointment("TEST001", "High", "Test Reason")
    assert appt['priority'] == "URGENT"
    assert appt['status'] == "Scheduled (Mock)"
    print("Calendar Service Passed")

def test_api_dashboard():
    print("Testing Dashboard API...")
    response = client.get("/")
    assert response.status_code == 200
    assert "CarePulseAI" in response.text
    print(" Dashboard Endpoint Passed")

def test_api_schedule():
    print("Testing Schedule API...")
    
    df = pd.read_csv('data/processed_patients.csv')
    if not df.empty:
        patient_id = df.iloc[0]['patient_id']
        response = client.post(f"/api/schedule/{patient_id}")
        assert response.status_code == 200
        json_resp = response.json()
        assert json_resp['status'] == "Scheduled (Mock)"
        print(f" Schedule Endpoint Passed for {patient_id}")
    else:
        print(" No data to test Schedule API")

if __name__ == "__main__":
    test_nlp()
    test_calendar()
    test_api_dashboard()
    test_api_schedule()
    print("\n ALL SYSTEMS GO! CarePulseAI is verified.")
