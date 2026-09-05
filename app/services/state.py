from datetime import datetime, timedelta, timezone
from app.config import settings

def is_fresh(timestamp):
    if timestamp is None:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp >= datetime.now(timezone.utc) - timedelta(seconds=settings.location_stale_seconds)
