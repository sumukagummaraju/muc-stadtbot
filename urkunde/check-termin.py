#!/usr/bin/env python3
"""
München Terminvereinbarung - Appointment Checker
Service: Einbürgerung (1071907) at location 10471

Polls the API every N minutes and emails you when a slot opens up for urkunde pickup before your target date.

Setup:
    pip install requests

    You need a Gmail "App Password" (not your regular password):
    1. Go to https://myaccount.google.com/security
    2. Enable 2-Step Verification if not already on
    3. Search for "App passwords" -> create one for "Mail"
    4. Paste the 16-char password into GMAIL_APP_PASSWORD below

Usage:
    python check_termin.py                         # checks every 5 min, target date 2026-06-18
    python check_termin.py --interval 10           # check every 10 minutes
    python check_termin.py --before 2026-05-01     # different cutoff date
    python check_termin.py --once                  # single check, good for cron
"""

import argparse
import time
import smtplib
import sys
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

# ── Configuration — edit these ────────────────────────────────────────────────

NOTIFY_EMAIL       = "your_email@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"   # <- paste your 16-char App Password here

DEFAULT_TARGET_DATE  = "2026-06-18"   # notify if any slot is strictly before this date
DEFAULT_INTERVAL_MIN = 15              # how often to poll (minutes)

# ── API details ───────────────────────────────────────────────────────────────

SERVICE_ID  = 1071907 # hardcoded for urkunde pickup
LOCATION_ID = 10471 # hardcoded for Einbürgerung office at LHS münchen

BOOKING_URL = (
    f"https://stadt.muenchen.de/buergerservice/terminvereinbarung.html"
    f"#/services/{SERVICE_ID}/locations/{LOCATION_ID}"
)

def build_api_url(start: date, end: date) -> str:
    return (
        f"https://www48.muenchen.de/buergeransicht/api/citizen/available-days-by-office/"
        f"?startDate={start.isoformat()}"
        f"&endDate={end.isoformat()}"
        f"&officeId={LOCATION_ID}"
        f"&serviceId={SERVICE_ID}"
        f"&serviceCount=1"
    )

HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://stadt.muenchen.de/",
}

# ── Email ─────────────────────────────────────────────────────────────────────

def send_email(subject: str, body: str, early_slots: list) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = NOTIFY_EMAIL
    msg["To"]      = NOTIFY_EMAIL

    slots_html = "".join(
        f'<li style="font-size:18px;padding:4px 0;"><strong>{d}</strong></li>'
        for d in early_slots
    )

    html = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:20px;">
      <h2 style="color:#1a4f8a;">Muenchen Einbuergerung &mdash; Early Slot Found!</h2>
      <p style="font-size:16px;">
        An appointment is now available <strong>before {DEFAULT_TARGET_DATE}</strong>!
      </p>
      <p style="font-size:16px;"><strong>Available dates:</strong></p>
      <ul>{slots_html}</ul>
      <br>
      <a href="{BOOKING_URL}"
         style="background:#1a4f8a;color:white;padding:14px 28px;
                text-decoration:none;border-radius:6px;font-size:16px;display:inline-block;">
        Book Now
      </a>
      <br><br>
      <hr>
      <small style="color:#888;">Sent by check_termin.py &mdash; running on your machine</small>
    </body></html>
    """

    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(NOTIFY_EMAIL, GMAIL_APP_PASSWORD)
        smtp.sendmail(NOTIFY_EMAIL, NOTIFY_EMAIL, msg.as_string())

    print(f"  -> Email sent to {NOTIFY_EMAIL}")


def send_test_email() -> None:
    """Send a test email to confirm credentials work."""
    print("Sending test email...")
    send_email(
        subject="check_termin.py — test email works!",
        body=f"Your appointment checker is configured correctly.\n\nIt will notify you when a slot opens before {DEFAULT_TARGET_DATE}.\n\nBooking URL: {BOOKING_URL}",
        early_slots=["(this is a test — no real slot found)"],
    )
    print("Test email sent successfully.")

# ── API fetch ─────────────────────────────────────────────────────────────────

def fetch_available_days() -> list:
    """Return sorted list of available date strings (YYYY-MM-DD) over next 6 months."""
    today = date.today()
    end   = today + timedelta(days=183)
    url   = build_api_url(today, end)

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    data = resp.json()

    # Handle both shapes:
    #   {"availableDays": [{"time": "2026-06-23", "providerIDs": "10471"}, ...]}
    #   or a plain list of strings / dicts
    if isinstance(data, dict):
        days_raw = data.get("availableDays", [])
    elif isinstance(data, list):
        days_raw = data
    else:
        days_raw = []

    available = []
    for entry in days_raw:
        if isinstance(entry, str):
            day_str = entry
        elif isinstance(entry, dict):
            day_str = entry.get("time") or entry.get("date") or ""
        else:
            continue
        if day_str:
            available.append(day_str[:10])   # keep YYYY-MM-DD only

    return sorted(set(available))

# ── Main loop ─────────────────────────────────────────────────────────────────

def check_once(target: date, last_notified: set) -> set:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Checking ... ", end="", flush=True)

    days  = fetch_available_days()
    early = [d for d in days if d < target.isoformat()]

    if early:
        new = [d for d in early if d not in last_notified]
        print(f"EARLY SLOT(S) FOUND: {early}")

        if new:
            slots_str = "\n".join(f"  - {d}" for d in early)
            body = (
                f"An Einbuergerung appointment is available before {target.isoformat()}!\n\n"
                f"Available dates:\n{slots_str}\n\n"
                f"Book here: {BOOKING_URL}"
            )
            send_email(
                subject=f"Einbuergerung slot on {early[0]} — book now!",
                body=body,
                early_slots=early,
            )
            last_notified.update(new)
        else:
            print(f"  (already notified about these slots)")
    else:
        next_few = ", ".join(days[:3]) if days else "none found"
        print(f"no early slots. Next available: {next_few}")

    return last_notified


def main():
    parser = argparse.ArgumentParser(
        description="Check Munich Einbuergerung appointment availability and email on early slot"
    )
    parser.add_argument(
        "--before",
        default=DEFAULT_TARGET_DATE,
        help=f"Notify if slot opens before this date (default: {DEFAULT_TARGET_DATE})"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_MIN,
        help=f"Polling interval in minutes (default: {DEFAULT_INTERVAL_MIN})"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check and exit (useful for cron)"
    )
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Send a test email and exit (to verify Gmail credentials)"
    )
    args = parser.parse_args()

    if GMAIL_APP_PASSWORD == "xxxx xxxx xxxx xxxx":
        print("ERROR: Please set your Gmail App Password in the script (GMAIL_APP_PASSWORD).")
        print("See setup instructions at the top of the file.")
        sys.exit(1)

    if args.test_email:
        send_test_email()
        return

    target = datetime.strptime(args.before, "%Y-%m-%d").date()

    print("=" * 60)
    print("  Muenchen Einbuergerung Appointment Checker")
    print(f"  Notify if slot before: {target.isoformat()}")
    print(f"  Email: {NOTIFY_EMAIL}")
    if not args.once:
        print(f"  Polling every {args.interval} minute(s). Ctrl+C to stop.")
    print("=" * 60)

    last_notified: set = set()

    if args.once:
        check_once(target, last_notified)
        return

    while True:
        try:
            last_notified = check_once(target, last_notified)
        except requests.HTTPError as e:
            print(f"  [HTTP error] {e}")
        except requests.RequestException as e:
            print(f"  [Network error] {e}")
        except smtplib.SMTPAuthenticationError:
            print("  [Email error] Gmail authentication failed — check your App Password.")
            print("  Continuing to poll, but notifications won't send until fixed.")
        except Exception as e:
            print(f"  [Unexpected error] {e}")

        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()