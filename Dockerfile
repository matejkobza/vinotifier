FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vinotifier.py .
COPY locales /app/locales
# We don't copy emails.csv or last_schedule.json here because we want to mount them as volumes
# to allow editing and persistence. But we can copy a default if needed.

CMD ["python", "vinotifier.py"]
