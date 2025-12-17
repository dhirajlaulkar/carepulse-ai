from src.calendar_service import CalendarService

def setup():
    print("Starting Google Calendar Authentication Setup...")
    print("A browser window should open shortly. Please log in with your Google account.")
    print("Ensure you allow the app to access your calendar.")
    
    service = CalendarService()
    
    if service.service:
        print("\nSUCCESS: Authentication complete! 'token.json' has been created.")
        print("You can now restart the application to use real scheduling.")
    else:
        print("\nFAILURE: Could not authenticate.")

if __name__ == "__main__":
    setup()
