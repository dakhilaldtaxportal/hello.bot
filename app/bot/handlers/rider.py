from telethon import events
from datetime import datetime, timezone
from app.db import SessionLocal
from app.models import User, RiderProfile
from app.bot.keyboards import main_menu, location_button
from app.config import settings

registration_state = {}
home_state = {}
zone_state = {}

async def begin_registration(event):
    registration_state[event.sender_id] = {"step": "phone"}
    await event.respond("Share your phone number.", buttons=[[__import__("telethon").Button.request_phone("📱 Share Phone")]])

async def handle_contact(event):
    data = registration_state.get(event.sender_id)
    if not data:
        return
    phone = getattr(event.message, "phone", None)
    if not phone:
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=event.sender_id).one()
        user.phone = phone
        db.commit()
    registration_state[event.sender_id] = {"step": "name"}
    await event.respond("Now send your name.")

async def handle_text(event):
    sid = event.sender_id
    if sid in registration_state and registration_state[sid].get("step") == "name":
        name = event.raw_text.strip()
        if not name:
            await event.respond("Please send a valid name.")
            return
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=sid).one()
            user.name = name
            db.commit()
        registration_state[sid] = {"step": "home"}
        await event.respond("Now share your permanent home location.", buttons=location_button())
        return
    if sid in home_state and home_state[sid]:
        return
    if sid in zone_state:
        try:
            radius = float(event.raw_text.strip())
        except ValueError:
            await event.respond(f"Send a number from {settings.zone_min_km} to {settings.zone_max_km}.")
            return
        if not settings.zone_min_km <= radius <= settings.zone_max_km:
            await event.respond(f"Radius must be {settings.zone_min_km}–{settings.zone_max_km} km.")
            return
        with SessionLocal() as db:
            rider = db.query(RiderProfile).join(User).filter(User.telegram_id == sid).one()
            rider.zone_radius_km = radius
            db.commit()
        zone_state.pop(sid, None)
        await event.respond(f"Home zone saved: {radius:g} km.", buttons=main_menu())

async def handle_location(event):
    loc = getattr(event.message, "geo", None)
    if not loc:
        return
    lat = getattr(loc, "lat", None)
    lon = getattr(loc, "long", None)
    if lat is None or lon is None:
        return
    sid = event.sender_id
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=sid).one_or_none()
        if not user:
            return
        rider = user.rider_profile
        rider.current_lat, rider.current_lon = lat, lon
        rider.last_location_at = datetime.now(timezone.utc)
        if registration_state.get(sid, {}).get("step") == "home":
            rider.home_lat, rider.home_lon = lat, lon
            registration_state.pop(sid, None)
            rider.online = False
            db.commit()
            await event.respond("Registration complete ✅", buttons=main_menu())
            return
        if home_state.get(sid):
            rider.home_lat, rider.home_lon = lat, lon
            home_state.pop(sid, None)
            db.commit()
            await event.respond("Permanent home location updated ✅", buttons=main_menu())
            return
        db.commit()

async def go_online(event):
    with SessionLocal() as db:
        rider = db.query(RiderProfile).join(User).filter(User.telegram_id == event.sender_id).one_or_none()
        user = db.query(User).filter_by(telegram_id=event.sender_id).one_or_none()
        if not rider or not rider.home_lat or user.suspended:
            await event.respond("Please complete registration first.")
            return
        if rider.busy:
            await event.respond("You are currently busy with an order.")
            return
        rider.online = True
        db.commit()
    await event.respond("You are ONLINE. Now share your Telegram live location so the bot can receive location updates.", buttons=location_button())

async def go_offline(event):
    with SessionLocal() as db:
        rider = db.query(RiderProfile).join(User).filter(User.telegram_id == event.sender_id).one_or_none()
        if rider:
            rider.online = False
            db.commit()
    await event.respond("You are OFFLINE.", buttons=main_menu())

async def change_home(event):
    home_state[event.sender_id] = True
    await event.respond("Share your new permanent home location.", buttons=location_button())

async def set_zone(event):
    zone_state[event.sender_id] = True
    await event.respond(f"Send your home-zone radius in km ({settings.zone_min_km}-{settings.zone_max_km}).")
