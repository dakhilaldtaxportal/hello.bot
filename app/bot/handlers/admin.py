from app.config import settings
from app.db import SessionLocal
from app.models import User, VendorProfile, PricingRule, BroadcastSetting

def is_admin(event):
    return event.sender_id in settings.admin_ids

async def add_vendor(event):
    if not is_admin(event):
        return
    await event.respond("Use: /add_vendor TELEGRAM_ID | NAME | PHONE | ADDRESS | LAT | LON")

async def add_vendor_command(event):
    if not is_admin(event):
        return
    raw = event.raw_text.split(" ", 1)
    if len(raw) != 2:
        await event.respond("Usage: /add_vendor TELEGRAM_ID | NAME | PHONE | ADDRESS | LAT | LON")
        return
    parts = [x.strip() for x in raw[1].split("|")]
    if len(parts) != 6:
        await event.respond("Invalid format.")
        return
    tid, name, phone, address, lat, lon = parts
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=int(tid)).one_or_none()
        if not user:
            user = User(telegram_id=int(tid), role="vendor", name=name, phone=phone)
            db.add(user)
            db.flush()
            db.add(VendorProfile(user_id=user.id, address=address, current_lat=float(lat), current_lon=float(lon)))
        else:
            user.role = "vendor"; user.name = name; user.phone = phone
            if not user.vendor_profile:
                db.add(VendorProfile(user_id=user.id, address=address, current_lat=float(lat), current_lon=float(lon)))
            else:
                user.vendor_profile.address = address
                user.vendor_profile.current_lat = float(lat)
                user.vendor_profile.current_lon = float(lon)
        db.commit()
    await event.respond("Vendor saved ✅")

async def pricing_command(event):
    if not is_admin(event): return
    parts = event.raw_text.split()
    if len(parts) != 4:
        await event.respond("Usage: /set_pricing BASE_KM BASE_CHARGE EXTRA_KM_CHARGE")
        return
    _, base_km, base_charge, extra = parts
    with SessionLocal() as db:
        row = db.query(PricingRule).order_by(PricingRule.id).first()
        if not row:
            row = PricingRule(); db.add(row)
        row.base_km=float(base_km); row.base_charge=float(base_charge); row.extra_km_charge=float(extra)
        db.commit()
    await event.respond("Delivery pricing saved ✅")

async def broadcast_rate(event):
    if not is_admin(event): return
    parts = event.raw_text.split()
    if len(parts) != 2:
        await event.respond("Usage: /set_broadcast_rate RATE_PER_KM")
        return
    with SessionLocal() as db:
        row = db.query(BroadcastSetting).order_by(BroadcastSetting.id).first()
        if not row:
            row = BroadcastSetting(); db.add(row)
        row.rider_rate_per_km=float(parts[1]); db.commit()
    await event.respond("Broadcast rider rate saved ✅")

async def search_phone(event):
    if not is_admin(event): return
    parts=event.raw_text.split(maxsplit=1)
    if len(parts)!=2:
        await event.respond("Usage: /search PHONE")
        return
    with SessionLocal() as db:
        users=db.query(User).filter(User.phone == parts[1].strip()).all()
        if not users:
            await event.respond("No exact phone match.")
            return
        text="\n".join(f"ID={u.telegram_id} role={u.role} name={u.name or '-'} suspended={u.suspended}" for u in users)
    await event.respond(text)

async def suspend(event, value):
    if not is_admin(event): return
    parts=event.raw_text.split(maxsplit=1)
    if len(parts)!=2:
        await event.respond(f"Usage: /{'suspend' if value else 'unsuspend'} PHONE")
        return
    with SessionLocal() as db:
        users=db.query(User).filter(User.phone == parts[1].strip()).all()
        if len(users)!=1:
            await event.respond("Need exactly one matching phone number.")
            return
        users[0].suspended=value
        if users[0].rider_profile and value:
            users[0].rider_profile.online=False
        db.commit()
    await event.respond(("Suspended" if value else "Unsuspended") + " ✅")
