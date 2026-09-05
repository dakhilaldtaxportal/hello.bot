from telethon import Button
from app.db import SessionLocal
from app.models import User, VendorProfile, Order, PricingRule
from app.services.maps import parse_coordinates, road_distance_km
from app.services.pricing import delivery_charge
from app.config import settings

post_state = {}

async def post_order_start(event):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=event.sender_id).one_or_none()
        if not user or user.role != "vendor" or user.suspended or not user.vendor_profile:
            await event.respond("Vendor access is not available.")
            return
        if user.vendor_profile.current_lat is None:
            await event.respond("Admin must set your current vendor location first.")
            return
    post_state[event.sender_id] = {"step": "customer"}
    await event.respond("Send customer name.")

async def post_order_text(event):
    state = post_state.get(event.sender_id)
    if not state:
        return
    value = event.raw_text.strip()
    if state["step"] == "customer":
        state["customer_name"] = value
        state["step"] = "phone"
        await event.respond("Send customer phone.")
    elif state["step"] == "phone":
        state["customer_phone"] = value
        state["step"] = "location"
        await event.respond("Send customer Google Maps link containing coordinates, or send a Telegram location.")
    elif state["step"] == "location":
        coords = parse_coordinates(value)
        if not coords:
            await event.respond("Could not find coordinates in that link. Send a coordinate-bearing Google Maps link or Telegram location.")
            return
        state["lat"], state["lon"] = coords
        state["step"] = "notes"
        await event.respond("Send order notes, or /skip.")
    elif state["step"] == "notes":
        await create_order(event, value)

async def post_order_location(event):
    state = post_state.get(event.sender_id)
    if not state or state["step"] != "location":
        return
    loc = getattr(event.message, "geo", None)
    if not loc:
        return
    state["lat"], state["lon"] = loc.lat, loc.long
    state["step"] = "notes"
    await event.respond("Send order notes, or /skip.")

async def create_order(event, notes):
    state = post_state.pop(event.sender_id)
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=event.sender_id).one()
        vendor = user.vendor_profile
        order = Order(
            vendor_id=vendor.id,
            customer_name=state["customer_name"],
            customer_phone=state["customer_phone"],
            customer_lat=state["lat"],
            customer_lon=state["lon"],
            customer_map_url=f"https://maps.google.com/?q={state['lat']},{state['lon']}",
            notes=None if notes == "/skip" else notes,
            order_type="normal",
            status="open",
        )
        db.add(order)
        db.flush()
        pricing = db.query(PricingRule).order_by(PricingRule.id).first()
        if not pricing:
            pricing = PricingRule(base_km=3, base_charge=50, extra_km_charge=20)
            db.add(pricing)
            db.flush()
        try:
            order.road_distance_km = await road_distance_km(
                vendor.current_lat, vendor.current_lon, order.customer_lat, order.customer_lon, settings.osrm_base_url
            )
            order.delivery_charge = delivery_charge(
                order.road_distance_km, pricing.base_km, pricing.base_charge, pricing.extra_km_charge
            )
        except Exception:
            order.status = "routing_failed"
            db.commit()
            await event.respond("Order saved but road-distance lookup failed. Admin can retry after routing service is available.")
            return
        db.commit()
        await event.respond(
            f"Order #{order.id} posted ✅\nRoad distance: {order.road_distance_km:.2f} km\n"
            f"Customer delivery charge: {order.delivery_charge:.2f} TK"
        )
