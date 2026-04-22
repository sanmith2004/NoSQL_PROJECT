from flask import Blueprint, request, jsonify
from services import mongo_service as ms
from services import redis_service as rs
from services import notification_service as ns
from utils.helpers import serialize

reg_bp = Blueprint("registrations", __name__)

# ─── POST /events/<id>/register ──────────────────────────────────────────────
@reg_bp.route("/events/<event_id>/register", methods=["POST"])
def register(event_id):
    data = request.get_json()
    name       = data.get("name", "").strip()
    email      = data.get("email", "").strip()
    department = data.get("department", "").strip()

    if not name or not email or not department:
        return jsonify({"error": "name, email, and department are required"}), 400

    event = ms.get_event_by_id(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Get or create student
    student = ms.get_or_create_student(name, email, department)
    student_id = str(student["_id"])

    # Check duplicate registration
    existing = ms.get_registration(event_id, student_id)
    if existing:
        return jsonify({"error": "Already registered for this event"}), 409

    # ── Redis seat decrement (concurrency-safe) ──
    redis_ok, remaining = rs.decrement_seat(event_id)

    if redis_ok is False:
        # Redis says no seats
        return jsonify({"error": "No seats available"}), 409

    if redis_ok is None:
        # Redis down — fallback: check MongoDB registered_count
        if event["registered_count"] >= event["max_seats"]:
            return jsonify({"error": "No seats available (fallback check)"}), 409

    # ── Enqueue in registration queue ──
    rs.enqueue_registration(event_id, student_id)

    # ── Save to MongoDB ──
    try:
        reg = ms.create_registration(event_id, student_id)
        ms.increment_registered_count(event_id)
    except Exception as e:
        # Rollback Redis seat on MongoDB failure
        if redis_ok:
            rs.increment_seat(event_id)
        return jsonify({"error": "Registration failed", "detail": str(e)}), 500

    # ── Pub/Sub notifications ──
    title = event.get("title", "")
    if redis_ok and remaining is not None:
        ns.check_and_notify_almost_full(event_id, title)

    return jsonify({
        "message": "Registration successful",
        "registration": serialize(reg),
        "available_seats": remaining if redis_ok else None
    }), 201

# ─── DELETE /events/<id>/register ────────────────────────────────────────────
@reg_bp.route("/events/<event_id>/register", methods=["DELETE"])
def cancel_registration(event_id):
    data = request.get_json()
    email = data.get("email", "").strip()
    if not email:
        return jsonify({"error": "email is required"}), 400

    event = ms.get_event_by_id(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    from database import get_db
    db = get_db()
    student = db.students.find_one({"email": email})
    if not student:
        return jsonify({"error": "Student not found"}), 404
    student_id = str(student["_id"])

    deleted = ms.delete_registration(event_id, student_id)
    if not deleted:
        return jsonify({"error": "Registration not found"}), 404

    ms.decrement_registered_count(event_id)

    # Restore Redis seat
    new_count = rs.increment_seat(event_id)

    # Publish seat-open notification
    ns.notify_seat_open(event_id, event.get("title", ""))

    return jsonify({
        "message": "Registration cancelled",
        "available_seats": new_count
    }), 200

# ─── GET /events/<id>/seats ──────────────────────────────────────────────────
@reg_bp.route("/events/<event_id>/seats", methods=["GET"])
def get_seats(event_id):
    event = ms.get_event_by_id(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    seats = rs.get_available_seats(event_id)
    if seats is None:
        # Fallback to MongoDB
        seats = event["max_seats"] - event["registered_count"]
        source = "mongodb_fallback"
    else:
        source = "redis"

    return jsonify({
        "event_id": event_id,
        "available_seats": seats,
        "max_seats": event["max_seats"],
        "registered_count": event["registered_count"],
        "source": source
    }), 200
