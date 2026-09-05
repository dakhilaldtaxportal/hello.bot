from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.models import RiderProfile, User, Order, OrderOffer, OfferStatus, OrderStatus
from app.services.geo import haversine_km, inside_radius
from app.services.state import is_fresh

def _excluded(order):
    return {int(x) for x in order.excluded_rider_ids.split(",") if x.strip()}

def _eligible_riders(db: Session, order: Order, vendor_lat, vendor_lon):
    riders = db.execute(
        select(RiderProfile, User)
        .join(User, User.id == RiderProfile.user_id)
        .where(
            RiderProfile.online.is_(True),
            RiderProfile.busy.is_(False),
            User.suspended.is_(False),
            RiderProfile.current_lat.is_not(None),
            RiderProfile.current_lon.is_not(None),
            RiderProfile.home_lat.is_not(None),
            RiderProfile.home_lon.is_not(None),
        )
    ).all()
    excluded = _excluded(order)
    result = []
    for rider, user in riders:
        if rider.id in excluded or not is_fresh(rider.last_location_at):
            continue
        if haversine_km(rider.current_lat, rider.current_lon, vendor_lat, vendor_lon) > settings.normal_search_radius_km:
            continue
        if not inside_radius(rider.home_lat, rider.home_lon, vendor_lat, vendor_lon, rider.zone_radius_km):
            continue
        if not inside_radius(rider.home_lat, rider.home_lon, order.customer_lat, order.customer_lon, rider.zone_radius_km):
            continue
        result.append((rider, user))
    result.sort(key=lambda x: haversine_km(x[0].current_lat, x[0].current_lon, vendor_lat, vendor_lon))
    return result

def create_next_offer(db: Session, order_id: int, vendor_lat: float, vendor_lon: float):
    # PostgreSQL row lock makes order assignment atomic across competing workers.
    order = db.execute(
        select(Order).where(Order.id == order_id).with_for_update()
    ).scalar_one()
    if order.status not in (OrderStatus.OPEN.value, OrderStatus.OFFERED.value):
        return None
    pending = db.execute(
        select(OrderOffer).where(
            OrderOffer.order_id == order_id,
            OrderOffer.status == OfferStatus.PENDING.value,
        ).with_for_update()
    ).scalar_one_or_none()
    if pending:
        return pending
    candidates = _eligible_riders(db, order, vendor_lat, vendor_lon)
    used = {x.rider_id for x in db.execute(select(OrderOffer).where(OrderOffer.order_id == order_id)).scalars()}
    candidate = next((r for r, _ in candidates if r.id not in used), None)
    if not candidate:
        return None
    now = datetime.now(timezone.utc)
    offer = OrderOffer(
        order_id=order.id,
        rider_id=candidate.id,
        status=OfferStatus.PENDING.value,
        offered_at=now,
        expires_at=now + timedelta(seconds=settings.offer_timeout_seconds),
    )
    order.status = OrderStatus.OFFERED.value
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer

def expire_offer(db: Session, offer_id: int):
    offer = db.execute(select(OrderOffer).where(OrderOffer.id == offer_id).with_for_update()).scalar_one_or_none()
    if not offer or offer.status != OfferStatus.PENDING.value:
        return None
    order = db.execute(select(Order).where(Order.id == offer.order_id).with_for_update()).scalar_one()
    offer.status = OfferStatus.EXPIRED.value
    offer.responded_at = datetime.now(timezone.utc)
    order.status = OrderStatus.OPEN.value
    db.commit()
    return order

def reject_offer(db: Session, offer_id: int):
    offer = db.execute(select(OrderOffer).where(OrderOffer.id == offer_id).with_for_update()).scalar_one_or_none()
    if not offer or offer.status != OfferStatus.PENDING.value:
        return None
    order = db.execute(select(Order).where(Order.id == offer.order_id).with_for_update()).scalar_one()
    offer.status = OfferStatus.REJECTED.value
    offer.responded_at = datetime.now(timezone.utc)
    order.status = OrderStatus.OPEN.value
    db.commit()
    return order

def accept_offer(db: Session, offer_id: int):
    offer = db.execute(select(OrderOffer).where(OrderOffer.id == offer_id).with_for_update()).scalar_one_or_none()
    if not offer or offer.status != OfferStatus.PENDING.value:
        return None
    now = datetime.now(timezone.utc)
    if offer.expires_at < now:
        offer.status = OfferStatus.EXPIRED.value
        order = db.execute(select(Order).where(Order.id == offer.order_id).with_for_update()).scalar_one()
        order.status = OrderStatus.OPEN.value
        db.commit()
        return None
    order = db.execute(select(Order).where(Order.id == offer.order_id).with_for_update()).scalar_one()
    rider = db.execute(select(RiderProfile).where(RiderProfile.id == offer.rider_id).with_for_update()).scalar_one()
    if order.status not in (OrderStatus.OPEN.value, OrderStatus.OFFERED.value) or rider.busy:
        db.rollback()
        return None
    offer.status = OfferStatus.ACCEPTED.value
    offer.responded_at = now
    order.status = OrderStatus.ACCEPTED.value
    order.assigned_rider_id = rider.id
    rider.busy = True
    rider.online = False
    db.commit()
    return order

def release_order(db: Session, order_id: int, rider_id: int):
    order = db.execute(select(Order).where(Order.id == order_id).with_for_update()).scalar_one_or_none()
    if not order or order.status != OrderStatus.ACCEPTED.value or order.assigned_rider_id != rider_id:
        return None
    rider = db.execute(select(RiderProfile).where(RiderProfile.id == rider_id).with_for_update()).scalar_one()
    excluded = _excluded(order)
    excluded.add(rider_id)
    order.excluded_rider_ids = ",".join(map(str, sorted(excluded)))
    rider.busy = False
    rider.online = True
    order.assigned_rider_id = None
    order.status = OrderStatus.OPEN.value
    db.commit()
    return order

def complete_order(db: Session, order_id: int, rider_id: int):
    order = db.execute(select(Order).where(Order.id == order_id).with_for_update()).scalar_one_or_none()
    if not order or order.status != OrderStatus.ACCEPTED.value or order.assigned_rider_id != rider_id:
        return None
    rider = db.execute(select(RiderProfile).where(RiderProfile.id == rider_id).with_for_update()).scalar_one()
    order.status = OrderStatus.COMPLETED.value
    rider.busy = False
    rider.online = False
    db.commit()
    return order
