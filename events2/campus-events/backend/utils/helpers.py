from datetime import datetime, timezone
from bson import ObjectId
import json

class JSONEncoder(json.JSONEncoder):
    """Custom encoder to handle ObjectId and datetime."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize(obj):
    """Recursively convert ObjectId/datetime in dicts/lists."""
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def seconds_until(dt: datetime) -> int:
    """Return seconds from now until dt (UTC). 0 if in the past."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = (dt - now).total_seconds()
    return max(0, int(delta))

def format_countdown(seconds: int) -> str:
    if seconds <= 0:
        return "Event started"
    days    = seconds // 86400
    hours   = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs    = seconds % 60
    parts = []
    if days:    parts.append(f"{days}d")
    if hours:   parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
