import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarService:
    def __init__(self):
        print("Initializing Real Google Calendar Service...")
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """
        Handles OAuth2 authentication flow.
        """
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}. Re-authenticating...")
                    self.creds = None
            
            if not self.creds:
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    # This will open a browser window on the server side if run locally
                    self.creds = flow.run_local_server(port=0)
                    
                    # Save the credentials for the next run
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())
                else:
                    print("ERROR: credentials.json not found. Calendar integration will fail.")
                    return

        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            print("Successfully connected to Google Calendar API")
        except Exception as e:
            print(f"Failed to build service: {e}")

    def schedule_appointment(self, patient_id, risk_level, reason):
        """
        Schedules a real appointment in Google Calendar.
        """
        if not self.service:
            print("Service not initialized. Attempting re-auth...")
            self.authenticate()
            if not self.service:
                return {"error": "Calendar service unavailable"}

        now = datetime.datetime.now()
        
        # Determine timing based on risk
        if risk_level == 'High':
            delay = datetime.timedelta(days=1) # High risk -> Tomorrow
            priority = "URGENT"
            color_id = '11' # Red
        elif risk_level == 'Medium':
            delay = datetime.timedelta(days=3)
            priority = "Standard"
            color_id = '5' # Yellow
        else:
            delay = datetime.timedelta(days=7)
            priority = "Routine"
            color_id = '2' # Green
            
        start_time = now + delay
        # Round to next hour
        start_time = start_time.replace(minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(hours=1)
        
        event = {
            'summary': f'[{priority}] Follow-up: {patient_id}',
            'location': 'Telemedicine Portal',
            'description': f'Risk Level: {risk_level}\nReason: {reason}\nPatient ID: {patient_id}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC', 
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'colorId': color_id,
        }

        try:
            event_result = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created: {event_result.get('htmlLink')}")
            
            return {
                "patient_id": patient_id,
                "time": start_time.strftime("%Y-%m-%d %H:%M"),
                "risk": risk_level,
                "priority": priority,
                "status": "Scheduled",
                "link": event_result.get('htmlLink')
            }
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"error": str(e)}

# Singleton instance
# Note: Instantiating this might trigger auth flow immediately if imported.
# To avoid blocking import, we can instantiate lazily or handle it in main.
# For now, let's keep it global but wrap auth in try/except block in init if we wanted to be safe
# But here we want to trigger it.
calendar_service = CalendarService()
