import datetime

class CalendarService:
    def __init__(self):
        print("Initializing Mock Google Calendar Service...")
        self.appointments = []

    def schedule_appointment(self, patient_id, risk_level, reason):
        """
        Simulates scheduling an appointment.
        High risk -> Next available slot within 24 hours.
        Medium risk -> Within 3 days.
        Low risk -> Within 1 week.
        """
        now = datetime.datetime.now()
        
        if risk_level == 'High':
            delay = datetime.timedelta(hours=1) # Mock: Schedule in 1 hour
            priority = "URGENT"
        elif risk_level == 'Medium':
            delay = datetime.timedelta(days=2)
            priority = "Standard"
        else:
            delay = datetime.timedelta(days=7)
            priority = "Routine"
            
        appointment_time = now + delay
        appointment = {
            "patient_id": patient_id,
            "time": appointment_time.strftime("%Y-%m-%d %H:%M"),
            "risk": risk_level,
            "reason": reason,
            "priority": priority,
            "status": "Scheduled (Mock)"
        }
        
        self.appointments.append(appointment)
        print(f"[CALENDAR] Scheduled {priority} for {patient_id} at {appointment['time']}")
        return appointment

# Singleton instance
calendar_service = CalendarService()
