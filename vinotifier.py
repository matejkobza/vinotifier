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
LOCALE = os.getenv("LOCALE", "en").lower()
DATA_FILE = "last_schedule.json"
LOCALES_DIR = "locales"

# Localization Loading
def load_strings():
    locale_file = os.path.join(LOCALES_DIR, f"{LOCALE}.json")
    default_file = os.path.join(LOCALES_DIR, "en.json")
    
    # Try loading selected locale
    if os.path.exists(locale_file):
        with open(locale_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    # Fallback to default (en)
    if os.path.exists(default_file):
        print(f"Locale {LOCALE} not found, falling back to en.")
        with open(default_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    # Fallback to hardcoded English if files are missing
    print("Warning: No locale files found!")
    return {
        "start_msg": "Starting Vinotifier...",
        "no_recipients": "No recipients found.",
        "email_sent": "Email sent to {}",
        "email_fail": "Failed to send email: {}",
        "missing_env": "Missing MYVAILLANT_USER or MYVAILLANT_PASS env vars",
        "no_prev_schedule": "No previous schedule found. Saving current state.",
        "changes_detected": "Changes detected!",
        "changes_email_intro": "The following changes were detected in your heating schedule:\n\n",
        "email_subject_change": "Heating Schedule Changed",
        "no_changes": "No changes detected.",
        "fetch_error": "Failed to fetch heater status or schedule: {}",
        "email_subject_error": "Vinotifier Error: Heater Unavailable",
        "new_zone": "New zone found: {name}",
        "zone_removed": "Zone removed: {name}",
        "schedule_changed": "Schedule changed for {name} on {day}.\nOld: {old}\nNew: {new}",
        "days": {
            "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
            "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday", "sunday": "Sunday"
        }
    }

STRINGS = load_strings()

def t(key, **kwargs):
    """Get localized string."""
    template = STRINGS.get(key, key)
    if isinstance(template, str):
        return template.format(**kwargs)
    return template

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
        print(t("no_recipients"))
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
        print(t("email_sent").format(recipients))
    except Exception as e:
        print(t("email_fail").format(e))

async def get_current_schedule():
    if not MYVAILLANT_USER or not MYVAILLANT_PASS:
        raise ValueError(t("missing_env"))

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
                            
                            # Convert minutes to HH:MM if integer
                            def format_time(val):
                                if isinstance(val, int):
                                    hours = val // 60
                                    minutes = val % 60
                                    return f"{hours:02d}:{minutes:02d}"
                                elif hasattr(val, 'strftime'):
                                    return val.strftime("%H:%M")
                                return str(val)

                            start_str = format_time(start)
                            end_str = format_time(end)
                            
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
            changes.append(t("new_zone", name=new_zone_data['name']))
            continue
        
        old_zone_data = old[key]
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            new_day = new_zone_data.get(day)
            old_day = old_zone_data.get(day)
            if new_day != old_day:
                # Localize day name
                day_map = t("days")
                day_name = day_map.get(day, day)
                changes.append(t("schedule_changed", name=new_zone_data['name'], day=day_name, old=old_day, new=new_day))
    
    # Check for removed zones
    for key in old:
        if key not in new:
            changes.append(t("zone_removed", name=old[key]['name']))

    return changes

async def main():
    print(t("start_msg"))
    recipients = read_emails()
    
    try:
        current_schedule = await get_current_schedule()
        last_schedule = load_last_schedule()
        
        if not last_schedule:
            print(t("no_prev_schedule"))
            save_current_schedule(current_schedule)
            return

        changes = compare_schedules(last_schedule, current_schedule)
        
        if changes:
            print(t("changes_detected"))
            body = t("changes_email_intro") + "\n\n".join(changes)
            send_email(t("email_subject_change"), body, recipients)
            save_current_schedule(current_schedule)
        else:
            print(t("no_changes"))
            
    except Exception as e:
        error_msg = t("fetch_error").format(str(e))
        print(error_msg)
        # Only send email if recipients are found
        if recipients:
            send_email(t("email_subject_error"), error_msg, recipients)

if __name__ == "__main__":
    asyncio.run(main())
