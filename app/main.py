from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
import uvicorn

app = FastAPI(title="CarePulseAI")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

DATA_FILE = 'data/processed_patients.csv'

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    df = load_data()
    
    patients = []
    stats = {'total': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}

    if not df.empty:
        # Calculate stats
        risk_counts = df['Risk Category'].value_counts().to_dict()
        stats['total'] = len(df)
        stats['high_risk'] = risk_counts.get('High', 0)
        stats['medium_risk'] = risk_counts.get('Medium', 0)
        stats['low_risk'] = risk_counts.get('Low', 0)
        
        # Convert NaN to None for JSON compatibility
        patients = df.where(pd.notnull(df), None).to_dict(orient='records')

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "patients": patients,
        "stats": stats
    })

@app.get("/api/patients")
async def get_patients():
    df = load_data()
    if df.empty:
        return []
    return df.where(pd.notnull(df), None).to_dict(orient='records')

from src.calendar_service import calendar_service

@app.post("/api/schedule/{patient_id}")
async def schedule_patient(patient_id: str):
    df = load_data()
    if df.empty:
        return {"error": "No data found"}
    
    patient = df[df['patient_id'] == patient_id]
    if patient.empty:
        return {"error": "Patient not found"}
    
    patient_data = patient.iloc[0]
    risk = patient_data['Risk Category']
    # Use symptoms as reason, or generic if empty
    symptoms = patient_data['Symptoms']
    reason = f"Follow-up for: {symptoms}" if symptoms else "General Follow-up"
    
    appointment = calendar_service.schedule_appointment(patient_id, risk, reason)
    return appointment

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
