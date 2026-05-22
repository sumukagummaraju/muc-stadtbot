#!/usr/bin/env python3
"""
Munich Passport/Ausweis Status Monitor
This script periodically checks the status of your passport or ID card application
Requirements: pip install requests
"""

import smtplib
import time
from email.mime.text import MIMEText
import requests

# ── Config ────────────────────────────────────────────────────────────────────

TRACKING_NUMBER      = "XXXXXXXXXX"          # Your tracking number - usually 10 alphanumeric chars, e.g. "XXXXXXXXXX"
DOCUMENT_TYPE        = "REISEPASS"            # "REISEPASS" or "BUNDESPERSONALAUSWEIS" (based on what you applied for)

GMAIL_ADDRESS        = "your_email@gmail.com" # Your Gmail address (must have 2FA enabled and an App Password created)
GMAIL_APP_KEY        = "xxxx xxxx xxxx xxxx"  # Google App Password, check https://myaccount.google.com/security to create one

POLL_INTERVAL_SECONDS = 3600                  # Number will determine how often to check (3600 = 1 hour, 5400 = 1.5 hours)

# ── API ───────────────────────────────────────────────────────────────────────

API_URL = (
    "https://mpdz-passverfolgung.muenchen.de"
    "/api/passstatusabfrage-backend-service/rest/ausweisstatus/search"
)

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": "https://stadt.muenchen.de/infos/status-personalausweis-reisepass.html",
    "Origin": "https://stadt.muenchen.de",
}

# ── Main ──────────────────────────────────────────────────────────────────────

def check_and_notify():
    resp = requests.post(
        API_URL,
        json={"nummer": TRACKING_NUMBER, "typ": DOCUMENT_TYPE},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    status   = data.get("status", "UNBEKANNT")
    pickup   = data.get("abholort", {})
    location = f"{pickup.get('name', '')} – {pickup.get('strasse', '')}".strip(" –")

    body = f"Status: {status}\nPickup: {location or 'n/a'}\nTracking: {TRACKING_NUMBER}"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Passport status: {status}"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = GMAIL_ADDRESS

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_KEY)
        smtp.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
    print(f"Sent: {status}")

while True:
    check_and_notify()
    time.sleep(POLL_INTERVAL_SECONDS)
