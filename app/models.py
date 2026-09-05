from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def utcnow():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class UserRole(str, Enum):
    RIDER = "rider"
    VENDOR = "vendor"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    OPEN = "open"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ROUTING_FAILED = "routing_failed"

class OfferStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    RELEASED = "released"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.RIDER.value)
    name: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(40), index=True)
    suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    rider_profile: Mapped["RiderProfile | None"] = relationship(back_populates="user", uselist=False)
    vendor_profile: Mapped["VendorProfile | None"] = relationship(back_populates="user", uselist=False)

class RiderProfile(Base):
    __tablename__ = "rider_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    home_lat: Mapped[float | None] = mapped_column(Float)
    home_lon: Mapped[float | None] = mapped_column(Float)
    zone_radius_km: Mapped[float] = mapped_column(Float, default=3)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    current_lat: Mapped[float | None] = mapped_column(Float)
    current_lon: Mapped[float | None] = mapped_column(Float)
    last_location_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    busy: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped[User] = relationship(back_populates="rider_profile")

class VendorProfile(Base):
    __tablename__ = "vendor_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    address: Mapped[str | None] = mapped_column(Text)
    current_lat: Mapped[float | None] = mapped_column(Float)
    current_lon: Mapped[float | None] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    user: Mapped[User] = relationship(back_populates="vendor_profile")

class PricingRule(Base):
    __tablename__ = "pricing_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_km: Mapped[float] = mapped_column(Float, default=3)
    base_charge: Mapped[float] = mapped_column(Float, default=50)
    extra_km_charge: Mapped[float] = mapped_column(Float, default=20)

class BroadcastSetting(Base):
    __tablename__ = "broadcast_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rider_rate_per_km: Mapped[float] = mapped_column(Float, default=20)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendor_profiles.id"), index=True)
    customer_name: Mapped[str] = mapped_column(String(150))
    customer_phone: Mapped[str | None] = mapped_column(String(40))
    customer_lat: Mapped[float] = mapped_column(Float)
    customer_lon: Mapped[float] = mapped_column(Float)
    customer_map_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    order_type: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(30), default=OrderStatus.OPEN.value, index=True)
    road_distance_km: Mapped[float | None] = mapped_column(Float)
    delivery_charge: Mapped[float | None] = mapped_column(Float)
    rider_extra_pay: Mapped[float | None] = mapped_column(Float)
    assigned_rider_id: Mapped[int | None] = mapped_column(ForeignKey("rider_profiles.id"), index=True)
    excluded_rider_ids: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class OrderOffer(Base):
    __tablename__ = "order_offers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("rider_profiles.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=OfferStatus.PENDING.value, index=True)
    offered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("order_id", "rider_id", name="uq_order_offer_rider"),
        Index("ix_offer_pending_order", "order_id", "status"),
    )
