# Telegram Food Delivery Bot — Final

Stack: Python 3.11+, Telethon, FastAPI, SQLAlchemy, PostgreSQL.

## Features
- Rider registration: Telegram phone, name, permanent home location.
- Change home address.
- Online/offline workflow with Telegram live-location instructions.
- Fresh-location/stale-location validation.
- Rider home-zone radius 1–10 km.
- Vendor registration by admin with phone/address/location.
- Vendor order posting with Telegram/Google Maps coordinate parsing.
- Road-distance calculation through OSRM by default (configurable).
- Admin-configurable delivery pricing and broadcast rider rate.
- Normal dispatch: vendor-to-rider search radius, rider home-zone checks for vendor and customer.
- One rider at a time; accept timeout, reject, release, complete.
- Broadcast: 5 km rider search and extra rider pay based on road distance.
- Admin search/suspend/unsuspend and vendor location editing.
- PostgreSQL row-locking for critical order/offer transitions.
- FastAPI /health endpoint.
- Optional internal self-ping; external UptimeRobot is recommended.
- Alembic migration setup.
- Automated tests for core services.

## Telegram limitation
A Telegram bot is not a native always-on GPS tracker. The bot can process Telegram live-location messages/edits that Telegram delivers. The rider must keep an active live-location share according to Telegram's behavior. The bot marks stale locations offline.

## Configuration
Copy `.env.example` to `.env` and set:
- BOT_TOKEN
- TELEGRAM_API_ID
- TELEGRAM_API_HASH
- DATABASE_URL
- ADMIN_IDS

Optional:
- ROUTING_PROVIDER=osrm
- OSRM_BASE_URL=https://router.project-osrm.org
- LOCATION_STALE_SECONDS=180
- OFFER_TIMEOUT_SECONDS=60
- NORMAL_SEARCH_RADIUS_KM=1
- BROADCAST_SEARCH_RADIUS_KM=5
- SELF_PING_URL=
- SELF_PING_INTERVAL_SECONDS=600

Do not put secrets in GitHub.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

## Tests
```bash
pytest -q
```

## Render
Use the included `render.yaml`. Create a PostgreSQL database in Render, copy its connection string to DATABASE_URL, and set Telegram secrets in the service environment.

A single worker/instance is recommended for the bot process unless the architecture is extended for distributed Telegram update handling.

## Important
This project calculates delivery fees and rider compensation; it does not process customer payments or wallet transfers.
