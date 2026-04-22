from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from services import mongo_service as ms
from services import redis_service as rs
from services import notification_service as ns
from utils.helpers import serialize, seconds_until

events_bp = Blueprint("events", __name__)

# ─── GET /events ─────────────────────────────────────────────────────────────
@events_bp.route("/events", methods=["GET"])
def list_events():
    event_type = request.args.get("type")
    filters = {"type": event_type} if event_type else {}
    events = ms.get_all_events(filters)
    for e in events:
        # Live seat count from Redis; fallback to MongoDB computed field
        seats = rs.get_available_seats(e["_id"])
        e["available_seats"] = seats if seats is not None else (e["max_seats"] - e["registered_count"])
        e["countdown_seconds"] = rs.get_event_countdown(e["_id"])
    return jsonify(serialize(events)), 200

# ─── GET /events/<id> ────────────────────────────────────────────────────────
@events_bp.route("/events/<event_id>", methods=["GET"])
def get_event(event_id):
    event = ms.get_event_by_id(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    seats = rs.get_available_seats(event_id)
    event["available_seats"] = seats if seats is not None else (event["max_seats"] - event["registered_count"])
    event["countdown_seconds"] = rs.get_event_countdown(event_id)
    return jsonify(serialize(event)), 200

# ─── POST /events ─────────────────────────────────────────────────────────────
@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()
    required = ["title", "date", "venue", "max_seats", "type"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Parse date
    try:
        if isinstance(data["date"], str):
            data["date"] = datetime.fromisoformat(data["date"])
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO 8601."}), 400

    # Validate type
    valid_types = ["workshop", "hackathon", "seminar", "guest_lecture"]
    if data["type"] not in valid_types:
        return jsonify({"error": f"type must be one of {valid_types}"}), 400

    # Ensure attributes is a list of {key, value}
    if "attributes" not in data:
        data["attributes"] = []

    event = ms.create_event(data)
    event_id = str(event["_id"])

    # Init Redis seat counter
    rs.init_seat_counter(event_id, data["max_seats"])

    # Set countdown TTL
    secs = seconds_until(data["date"])
    rs.set_event_countdown(event_id, secs)

    # Publish new-event notification
    ns.notify_event_created(event)

    return jsonify(serialize(event)), 201
