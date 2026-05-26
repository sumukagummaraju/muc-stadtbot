# muc-stadtbot

> Polling the Munich KVR for an earlier appointment — so that I didn't have to manually check them.

There are two stages I used scripts:

1. When I wanted to advance my appointment to pick up my certificate.
2. When I wanted to know status of my ausweis and passport, and when it's available for pickup.

---

## Background

While on a vacation watching whales in the beautiful Vancouver region 🐳, I received a notification from the Munich **Kreisverwaltungsreferat (KVR)** that my citizenship certificate was ready for pickup. The only available appointment slot was too far away, and I already had things planned in the pipeline. I booked a later date as fallback, but instantly started thinking about ways to get an earlier one.

After understanding the request/response structures of the APIs being called, I asked Claude to write a script to automate this for me.

## Why

- I was NOT going to refresh the booking portal now and then, waiting for a sooner slot to pop up.
- I still wanted to book the appointment myself — I'm not quite comfortable with AI making decisions on my behalf (yet!) — but I wanted to be **notified by email the moment an earlier slot opened up**.

## How it ran

- A lightweight polling script, running on a remote server. 🖥️
- Big thanks to my better half and her remote server. 🙏

## What's in here

| File                                   | Description                                                            |
| -------------------------------------- | ---------------------------------------------------------------------- |
| `urkunde/check-termin.py`              | Script checking earlier appointment slots for certificate pickup       |
| `ausweis-pass/passport_monitor.py`     | Core polling script that checks for earlier passport appointment slots |
| `ausweis-pass/run_passport_monitor.sh` | Shell wrapper to run the passportmonitor                               |

## Steps to check earlier appointment dates for certificate pickup

1. Just run the python script (see usage in the script)

## Steps to check whether the ausweis & passport are ready for pickup

1. Fill in necessary details in passport_monitor.
2. Navigate into ausweis-pass directory.
3. Run shell script `sh run_passport_monitor.sh`
