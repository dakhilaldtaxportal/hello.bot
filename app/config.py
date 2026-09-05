import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _int_set(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}

@dataclass(frozen=True)
class Settings:
    bot_token: str
    telegram_api_id: int
    telegram_api_hash: str
    database_url: str
    admin_ids: set[int]
    routing_provider: str
    osrm_base_url: str
    location_stale_seconds: int
    offer_timeout_seconds: int
    normal_search_radius_km: float
    broadcast_search_radius_km: float
    zone_min_km: int
    zone_max_km: int
    self_ping_url: str
    self_ping_interval_seconds: int

def load_settings() -> Settings:
    required = ["BOT_TOKEN", "TELEGRAM_API_ID", "TELEGRAM_API_HASH", "DATABASE_URL", "ADMIN_IDS"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))
    return Settings(
        bot_token=os.environ["BOT_TOKEN"],
        telegram_api_id=int(os.environ["TELEGRAM_API_ID"]),
        telegram_api_hash=os.environ["TELEGRAM_API_HASH"],
        database_url=os.environ["DATABASE_URL"],
        admin_ids=_int_set(os.environ["ADMIN_IDS"]),
        routing_provider=os.getenv("ROUTING_PROVIDER", "osrm"),
        osrm_base_url=os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/"),
        location_stale_seconds=int(os.getenv("LOCATION_STALE_SECONDS", "180")),
        offer_timeout_seconds=int(os.getenv("OFFER_TIMEOUT_SECONDS", "60")),
        normal_search_radius_km=float(os.getenv("NORMAL_SEARCH_RADIUS_KM", "1")),
        broadcast_search_radius_km=float(os.getenv("BROADCAST_SEARCH_RADIUS_KM", "5")),
        zone_min_km=int(os.getenv("ZONE_MIN_KM", "1")),
        zone_max_km=int(os.getenv("ZONE_MAX_KM", "10")),
        self_ping_url=os.getenv("SELF_PING_URL", ""),
        self_ping_interval_seconds=int(os.getenv("SELF_PING_INTERVAL_SECONDS", "600")),
    )

settings = load_settings()
