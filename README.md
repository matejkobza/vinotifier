# Vinotifier

A notifier application for myVAILLANT schedule changes.

## Features
- Checks for heating schedule changes.
- Notifies via email on changes.
- Notifies via email if heater is unavailable (fetch fails).

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   Create a `.env` file or export the following variables:
   ```bash
   export MYVAILLANT_USER="your_email"
   export MYVAILLANT_PASS="your_password"
   export MYVAILLANT_COUNTRY="slovakia" # or germany, etc.
   export MYVAILLANT_BRAND="vaillant" # or saunier_duval, bulex, etc.
   export LOCALE="sk" # or en (default)
   export TZ="Europe/Bratislava"
   
   export SMTP_SERVER="smtp.gmail.com"
   export SMTP_PORT=587
   export SMTP_USER="your_email@gmail.com"
   export SMTP_PASSWORD="your_app_password"
   export SENDER_EMAIL="your_email@gmail.com"
   ```

3. Add recipients to `emails.csv`:
   ```csv
   email
   recipient1@example.com
   recipient2@example.com
   ```

## Docker Usage

1. **Build and Run:**
   ```bash
   docker-compose up --build
   ```

2. **Run in Background (Cron alternative):**
   The container exits after running once. To run periodically, use `cron` on the host:
   ```bash
   0 * * * * cd /path/to/vinotifier && docker-compose up >> vinotifier.log 2>&1
   ```

## Localization

Localization strings are stored in the `locales/` directory.
- `en.json`: English (default)
- `sk.json`: Slovak

To add a new language, create a new JSON file (e.g., `de.json`) and set `LOCALE="de"` in your `.env` file.

## Troubleshooting

If you suspect connection issues, try running the helper scripts manually (ensure `.env` is loaded):

**1. Check myVAILLANT connection:**
```bash
python3 check_connection.py
```

**2. Check Email connection:**
```bash
python3 check_email.py
```
This script attempts to send a test email to the SMTP user address.
