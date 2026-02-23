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

## Usage

Run the script manually:
```bash
python3 vinotifier.py
```

## Scheduling (Cron)

To check every hour, add this to your crontab (`crontab -e`):

```bash
0 * * * * cd /path/to/vinotifier && python3 vinotifier.py >> vinotifier.log 2>&1
```
