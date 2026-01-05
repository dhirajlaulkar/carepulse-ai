# CarePulseAI
**AI-Driven Patient Follow-Up and Health Outcome Prediction System**

## Overview
CarePulseAI analyzes doctor-patient conversations from CSV logs to identify high-risk patients using NLP and Sentiment Analysis. It provides a real-time dashboard for doctors to monitor patient risks and automatically prioritizes follow-up appointments via a smart scheduling system (integrated with Google Calendar).

## Features
- **Data Ingestion**: Robust parsing of conversation logs.
- **NLP Engine**: Extracts high-risk symptoms (e.g., "chest pain", "suicidal") and analyzes sentiment.
- **Risk Prediction**: Classifies patients into High/Medium/Low risk based on symptoms and emotional tone.
- **Smart Scheduling**: Automatically prioritizes high-risk patients for urgent slots.
- **Modern Dashboard**: High-premium dark-mode UI built with FastAPI and Jinja2.

## Installation

1. **Clone & Setup**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Data Processing**:
   Place your `patients.csv` in `data/` and run the analysis pipeline:
   ```bash
   python -m src.analysis_pipeline
   ```
   This generates `data/processed_patients.csv` with risk scores.

3. **Run the Dashboard**:
   ```bash
   python -m app.main
   ```
   Open your browser to `http://127.0.0.1:8000`.

## Project Structure
- `data/`: Dataset storage.
- `src/`: Core logic (Data loading, NLP, Risk Model, Calendar Service).
- `app/`: FastAPI application and UI templates.
- `verify_system.py`: End-to-end system verification script.

## Tech Stack
- **Backend**: FastAPI
- **Data-Science**: Pandas, NLTK, TextBlob, Scikit-learn
- **Frontend**: HTML5, CSS3 (Glassmorphism), Chart.js
- **Integration**: Google Calendar API Service
