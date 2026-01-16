from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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

import json

import datetime

DATA_FILE = 'data/processed_patients.csv'
SCHEDULED_FILE = 'data/scheduled_patients.json'
SETTINGS_FILE = 'data/settings.json'

def load_settings():
    defaults = {'high_threshold': 90, 'medium_threshold': 50, 'per_page': 15}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
                defaults.update(saved)
                return defaults
        except:
            return defaults
    return defaults

def save_settings(settings):
    current = load_settings()
    current.update(settings)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(current, f)

def load_scheduled_data():
    if os.path.exists(SCHEDULED_FILE):
        try:
            with open(SCHEDULED_FILE, 'r') as f:
                data = json.load(f)
                # Migration: if using old list format, convert to dict with future time
                if isinstance(data, list):
                    future = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
                    return {pid: future for pid in data}
                return data
        except:
            return {}
    return {}

def save_scheduled_id(patient_id, timestamp=None):
    data = load_scheduled_data()
    if not timestamp:
        timestamp = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
    data[patient_id] = timestamp
    with open(SCHEDULED_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Parse 'Symptoms' column from string representation to actual list
        if 'Symptoms' in df.columns:
            df['Symptoms'] = df['Symptoms'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
        
        # Recalculate Risk Category based on Settings
        settings = load_settings()
        high_thresh = int(settings.get('high_threshold', 90))
        med_thresh = int(settings.get('medium_threshold', 50))

        def calculate_risk(score):
            if score >= high_thresh: return 'High'
            if score >= med_thresh: return 'Medium'
            return 'Low'

        if 'Risk Score' in df.columns:
            df['Risk Category'] = df['Risk Score'].apply(calculate_risk)

        # Merge Scheduled Status
        scheduled_data = load_scheduled_data()
        now_str = datetime.datetime.now().isoformat()

        def get_status(pid):
            if pid not in scheduled_data:
                return 'Pending'
            timestamp = scheduled_data[pid]
            if timestamp < now_str:
                return 'Addressed'
            return 'Scheduled'

        df['Status'] = df['patient_id'].apply(get_status)
        
        return df
    return pd.DataFrame()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, page: int = 1):
    df = load_data()
    settings = load_settings()
    stats = {'total': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
    patients = []
    PER_PAGE = int(settings.get('per_page', 15))
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
    settings = load_settings()
    patients = []
    PER_PAGE = int(settings.get('per_page', 15))
    
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

@app.get("/api/settings")
async def get_settings_api():
    return load_settings()

@app.post("/api/settings")
async def update_settings_api(request: Request):
    new_settings = await request.json()
    save_settings(new_settings)
    return {"status": "success", "settings": load_settings()}

@app.get("/api/patients")
async def get_patients():
    df = load_data()
    if df.empty:
        return []
    return df.where(pd.notnull(df), None).to_dict(orient='records')

from src.calendar_service import calendar_service

@app.post("/api/schedule/{patient_id}")
async def schedule_patient(patient_id: str, request: Request):
    df = load_data()
    if df.empty:
        return {"error": "No data found"}
    
    # Extract patient details for the logic
    patient = df[df['patient_id'] == patient_id].iloc[0]
    risk_level = patient.get('Risk Category', 'Low')
    reason = f"Symptoms: {', '.join(patient.get('Symptoms', []))}"

    # 1. Call Google Calendar API
    result = calendar_service.schedule_appointment(patient_id, risk_level, reason)
    
    if "error" in result:
        print(f"Calendar Error: {result['error']}")
        # Fallback: Just mark as scheduled locally if API fails (or return error to UI)
        # For now, let's return error so user knows
        return JSONResponse(status_code=500, content={"message": result['error']})

    # 2. Persist scheduled status with ACTUAL time from calendar
    scheduled_time = result.get('time') # Expecting ISO format or similar if changed
    # The service returns formatted string "YYYY-MM-DD HH:MM", but save_scheduled_id expects ISO for comparison?
    # actually save_scheduled_id stores whatever we pass. load_data compares it.
    # load_data compares with now_str (ISO). 
    # Let's ensure we store ISO format for consistency.
    # The service returns 'time' as string. The service ALSO has 'link'.
    
    # Let's recreate ISO from the service logic or just use the one we pass?
    # actually the service creates 'start_time' datetime object.
    # We should update the service or just parse the returned string. 
    # Better yet, let's modify the service to return isoformat in a bit or just parse here.
    # Service returns: start_time.strftime("%Y-%m-%d %H:%M") 
    
    # Quick fix: allow service to do its thing, but we want to save a robust timestamp. 
    # Let's just generate a compliant timestamp here based on the risk logic again OR 
    # (Cleaner) Trust the service knows best. 
    
    # Re-calculating for storage consistency (since service returns pretty string):
    # Actually, let's just use the current time + 1 day/3days etc as a proxy for "when is it addressed"
    # The 'Addressed' logic compares THIS stored timestamp with NOW. 
    # If Stored < Now, it's Addressed.
    # So we should store the Meeting Time.
    
    # Let's just update save_scheduled_id to accept what we have.
    timestamp = result.get('time')
    # Use proper ISO format for string comparison
    try:
        dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        timestamp = dt.isoformat()
    except:
        timestamp = datetime.datetime.now().isoformat()

    save_scheduled_id(patient_id, timestamp)
    
    return {
        "status": "Scheduled", 
        "patient_id": patient_id, 
        "link": result.get('link'),
        "time": result.get('time')
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
