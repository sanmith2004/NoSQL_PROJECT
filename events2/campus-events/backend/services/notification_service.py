import json
from services.redis_service import publish, get_available_seats

CHANNEL_NEW       = "events:new"
CHANNEL_ALMOSTFULL = "events:almostfull"
CHANNEL_SEATOPEN  = "events:seatopen"
CHANNEL_CANCELLED = "events:cancelled"

def notify_event_created(event: dict):
    payload = json.dumps({
        "type": "new_event",
        "event_id": str(event["_id"]),
        "title": event["title"],
        "date": str(event["date"]),
        "venue": event["venue"],
        "max_seats": event["max_seats"]
    })
    publish(CHANNEL_NEW, payload)

def notify_almost_full(event_id: str, title: str, remaining: int):
    payload = json.dumps({
        "type": "almost_full",
        "event_id": event_id,
        "title": title,
        "remaining_seats": remaining
    })
    publish(CHANNEL_ALMOSTFULL, payload)

def notify_seat_open(event_id: str, title: str):
    payload = json.dumps({
        "type": "seat_open",
        "event_id": event_id,
        "title": title
    })
    publish(CHANNEL_SEATOPEN, payload)

def check_and_notify_almost_full(event_id: str, title: str):
    """Publish almost-full notification if seats drop below 5."""
    remaining = get_available_seats(event_id)
    if remaining is not None and 0 <= remaining < 5:
        notify_almost_full(event_id, title, remaining)
