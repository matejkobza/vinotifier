import asyncio
import csv
import smtplib
import json
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from myPyllant.api import MyPyllantAPI
from myPyllant.models import System, Zone, ZoneTimeProgram

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "user@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "password")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "notifier@example.com")

MYVAILLANT_USER = os.getenv("MYVAILLANT_USER")
MYVAILLANT_PASS = os.getenv("MYVAILLANT_PASS")
MYVAILLANT_COUNTRY = os.getenv("MYVAILLANT_COUNTRY", "germany")

MYVAILLANT_BRAND = os.getenv("MYVAILLANT_BRAND", "vaillant")
DATA_FILE = "last_schedule.json"

def read_emails(csv_file='emails.csv'):
    emails = []
    try:
        with open(csv_file, newline='') as f:
            reader = csv.reader(f)
            # Check if header exists
            first_row = next(reader, None)
            if first_row:
                 if '@' in first_row[0]: # primitive check if it's an email or header
                     emails.append(first_row[0])
                 # continue reading
                 for row in reader:
                     if row:
                         emails.append(row[0])
    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
    return emails

def send_email(subject, body, recipients):
    if not recipients:
        print("No recipients found.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        print(f"Email sent to {recipients}")
    except Exception as e:
        print(f"Failed to send email: {e}")

async def get_current_schedule():
    if not MYVAILLANT_USER or not MYVAILLANT_PASS:
        raise ValueError("Missing MYVAILLANT_USER or MYVAILLANT_PASS env vars")

    async with MyPyllantAPI(MYVAILLANT_USER, MYVAILLANT_PASS, MYVAILLANT_BRAND, MYVAILLANT_COUNTRY) as api:
        systems = []
        async for system in api.get_systems():
            systems.append(system)
        
        # Extract schedule data
        # Structure: System -> Zones -> Heating -> TimeProgram
        schedule_data = {}
        
        for system in systems:
            for zone in system.zones:
                if zone.heating:
                    program = zone.heating.time_program_heating
                    # Helper to serialize time program list
                    def serialize_program(day_program):
                        # Handle potential attribute variations
                        res = []
                        for s in day_program:
                            start = getattr(s, 'start_time', getattr(s, 'start', None))
                            end = getattr(s, 'end_time', getattr(s, 'end', None))
                            setpoint = getattr(s, 'setpoint', None)
                            
                            start_str = start.strftime("%H:%M") if hasattr(start, 'strftime') else str(start)
                            end_str = end.strftime("%H:%M") if hasattr(end, 'strftime') else str(end)
                            
                            res.append({"start": start_str, "end": end_str, "setpoint": setpoint})
                        return res

                    # Store as serializable dict
                    schedule_data[f"{system.id}_{zone.index}"] = {
                        "name": zone.name,
                        "monday": serialize_program(program.monday),
                        "tuesday": serialize_program(program.tuesday),
                        "wednesday": serialize_program(program.wednesday),
                        "thursday": serialize_program(program.thursday),
                        "friday": serialize_program(program.friday),
                        "saturday": serialize_program(program.saturday),
                        "sunday": serialize_program(program.sunday),
                    }
        return schedule_data

def load_last_schedule():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_current_schedule(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def compare_schedules(old, new):
    changes = []
    # Check for new or changed zones
    for key, new_zone_data in new.items():
        if key not in old:
            changes.append(f"New zone found: {new_zone_data['name']}")
            continue
        
        old_zone_data = old[key]
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            new_day = new_zone_data.get(day)
            old_day = old_zone_data.get(day)
            if new_day != old_day:
                changes.append(f"Schedule changed for {new_zone_data['name']} on {day}.\nOld: {old_day}\nNew: {new_day}")
    
    # Check for removed zones
    for key in old:
        if key not in new:
            changes.append(f"Zone removed: {old[key]['name']}")

    return changes

async def main():
    print("Starting Vinotifier...")
    recipients = read_emails()
    
    try:
        current_schedule = await get_current_schedule()
        last_schedule = load_last_schedule()
        
        if not last_schedule:
            print("No previous schedule found. Saving current state.")
            save_current_schedule(current_schedule)
            return

        changes = compare_schedules(last_schedule, current_schedule)
        
        if changes:
            print("Changes detected!")
            body = "The following changes were detected in your heating schedule:\n\n" + "\n\n".join(changes)
            send_email("Heating Schedule Changed", body, recipients)
            save_current_schedule(current_schedule)
        else:
            print("No changes detected.")
            
    except Exception as e:
        error_msg = f"Failed to fetch heater status or schedule: {str(e)}"
        print(error_msg)
        # Only send email if recipients are found
        if recipients:
            send_email("Vinotifier Error: Heater Unavailable", error_msg, recipients)

if __name__ == "__main__":
    asyncio.run(main())
