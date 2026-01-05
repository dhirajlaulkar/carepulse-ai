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

import ast

DATA_FILE = 'data/processed_patients.csv'

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Parse 'Symptoms' column from string representation to actual list
        if 'Symptoms' in df.columns:
            df['Symptoms'] = df['Symptoms'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
        return df
    return pd.DataFrame()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, page: int = 1):
    df = load_data()
    stats = {'total': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
    patients = []
    PER_PAGE = 15
    total_pages = 1

    if not df.empty:
        # Calculate stats (global)
        risk_counts = df['Risk Category'].value_counts().to_dict()
        stats['total'] = len(df)
        stats['high_risk'] = risk_counts.get('High', 0)
        stats['medium_risk'] = risk_counts.get('Medium', 0)
        stats['low_risk'] = risk_counts.get('Low', 0)
        
        # Filter by risk if needed
        # Note: We filter BEFORE pagination, but AFTER calculating global stats? 
        # Usually stats show "Total" but table shows filtered. 
        # Let's align with that.
        
        df_filtered = df.copy()
        
        # Get filter from query param, default 'all'
        risk_filter = request.query_params.get('risk_filter', 'all')
        
        if risk_filter and risk_filter.lower() != 'all':
             df_filtered = df_filtered[df_filtered['Risk Category'] == risk_filter]

        # Sort by Risk Score descending (High Risk first)
        df_sorted = df_filtered.sort_values(by='Risk Score', ascending=False)
        
        # Pagination
        total_records = len(df_sorted)
        total_pages = (total_records + PER_PAGE - 1) // PER_PAGE
        if total_pages < 1: total_pages = 1
        
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        df_paginated = df_sorted.iloc[start:end]
        patients = df_paginated.where(pd.notnull(df_paginated), None).to_dict(orient='records')

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "patients": patients,
        "stats": stats,
        "current_page": page,
        "total_pages": total_pages,
        "current_filter": request.query_params.get('risk_filter', 'all')
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    return templates.TemplateResponse("settings.html", {
        "request": request
    })

@app.get("/partials/patients", response_class=HTMLResponse)
async def get_patient_rows(request: Request, page: int = 1, risk_filter: str = 'all'):
    df = load_data()
    patients = []
    PER_PAGE = 15
    
    if not df.empty:
        df_filtered = df.copy()
        if risk_filter and risk_filter.lower() != 'all':
             df_filtered = df_filtered[df_filtered['Risk Category'] == risk_filter]

        df_sorted = df_filtered.sort_values(by='Risk Score', ascending=False)
        total_records = len(df_sorted)
        
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        df_paginated = df_sorted.iloc[start:end]
        patients = df_paginated.where(pd.notnull(df_paginated), None).to_dict(orient='records')
        
    return templates.TemplateResponse("patient_rows.html", {
        "request": request,
        "patients": patients
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

    symptoms = patient_data['Symptoms']
    reason = f"Follow-up for: {symptoms}" if symptoms else "General Follow-up"
    
    appointment = calendar_service.schedule_appointment(patient_id, risk, reason)
    return appointment

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
