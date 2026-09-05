from telethon import Button
from app.db import SessionLocal
from app.models import OrderOffer, Order, User, VendorProfile
from app.services.dispatch import accept_offer, reject_offer, release_order, complete_order, create_next_offer
from app.bot.formatting import order_text
from app.config import settings

async def offer_message(client, offer):
    with SessionLocal() as db:
        order=db.get(Order, offer.order_id)
        vendor=db.get(VendorProfile, order.vendor_id)
        vu=db.get(User, vendor.user_id)
        rider=db.get(__import__("app.models", fromlist=["RiderProfile"]).RiderProfile, offer.rider_id)
        ru=db.get(User, rider.user_id)
        text=order_text(order, vu.name or "Vendor", vu.phone)
        await client.send_message(ru.telegram_id, text, buttons=[
            [Button.inline("✅ Accept", data=f"accept:{offer.id}"), Button.inline("❌ Reject", data=f"reject:{offer.id}")]
        ])

async def callback(event):
    data=event.data.decode()
    action, raw_id=data.split(":",1)
    offer_id=int(raw_id)
    with SessionLocal() as db:
        offer=db.get(OrderOffer, offer_id)
        if not offer:
            await event.answer("Offer not found.", alert=True); return
        rider=__import__("app.models", fromlist=["RiderProfile"]).RiderProfile
        rp=db.get(rider, offer.rider_id)
        user=db.get(User, rp.user_id)
        if user.telegram_id != event.sender_id:
            await event.answer("This offer is not for you.", alert=True); return
        if action=="accept":
            order=accept_offer(db, offer_id)
            if not order:
                await event.answer("Offer expired or unavailable.", alert=True); return
            await event.edit("✅ Order accepted. You are now busy with this order.")
        else:
            order=reject_offer(db, offer_id)
            if not order:
                await event.answer("Offer is no longer active.", alert=True); return
            await event.edit("❌ Rejected.")
            vendor=db.get(__import__("app.models", fromlist=["VendorProfile"]).VendorProfile, order.vendor_id)
            offer2=create_next_offer(db, order.id, vendor.current_lat, vendor.current_lon)
            if offer2:
                await offer_message(event.client, offer2)

async def release(event):
    order_id=int(event.pattern_match.group(1))
    with SessionLocal() as db:
        rp=db.query(__import__("app.models", fromlist=["RiderProfile"]).RiderProfile).join(User).filter(User.telegram_id==event.sender_id).one()
        order=release_order(db, order_id, rp.id)
        if not order:
            await event.respond("Cannot release this order.")
            return
        vendor=db.get(__import__("app.models", fromlist=["VendorProfile"]).VendorProfile, order.vendor_id)
        offer=create_next_offer(db, order.id, vendor.current_lat, vendor.current_lon)
        if offer:
            await offer_message(event.client, offer)
    await event.respond("Order released and returned to dispatch.")

async def complete(event):
    order_id=int(event.pattern_match.group(1))
    with SessionLocal() as db:
        rp=db.query(__import__("app.models", fromlist=["RiderProfile"]).RiderProfile).join(User).filter(User.telegram_id==event.sender_id).one()
        order=complete_order(db, order_id, rp.id)
    await event.respond("Order completed ✅" if order else "Cannot complete this order.")
