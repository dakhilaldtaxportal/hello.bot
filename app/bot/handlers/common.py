from telethon import events, Button
from app.db import SessionLocal
from app.models import User, RiderProfile
from app.bot.keyboards import main_menu, location_button

async def start(event):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=event.sender_id).one_or_none()
        if not user:
            user = User(telegram_id=event.sender_id, role="rider")
            db.add(user)
            db.flush()
            db.add(RiderProfile(user_id=user.id))
            db.commit()
    await event.respond("Welcome! Use /registration to create your rider profile.", buttons=main_menu())

async def registration(event):
    await event.respond("Please share your phone number using Telegram's contact button.", buttons=[Button.request_phone("📱 Share Phone")])
