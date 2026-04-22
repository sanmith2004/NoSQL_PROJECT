from flask import Blueprint, jsonify, request
from services import mongo_service as ms
from services import redis_service as rs
from utils.helpers import serialize

admin_bp = Blueprint("admin", __name__)

# ─── GET /dashboard ──────────────────────────────────────────────────────────
@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    events = ms.get_all_events()
    total_events = len(events)
    total_registrations = sum(e.get("registered_count", 0) for e in events)
    students = ms.get_all_students()

    # Per-type breakdown
    type_counts = {}
    for e in events:
        t = e.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    return jsonify({
        "total_events": total_events,
        "total_registrations": total_registrations,
        "total_students": len(students),
        "events_by_type": type_counts
    }), 200

# ─── GET /admin/analytics ────────────────────────────────────────────────────
@admin_bp.route("/admin/analytics", methods=["GET"])
def analytics():
    return jsonify({
        "highest_registrations": serialize(ms.agg_highest_registrations()),
        "dept_participation":     serialize(ms.agg_dept_participation()),
        "most_active_students":   serialize(ms.agg_most_active_students()),
        "attendance_rate_by_type": serialize(ms.agg_attendance_rate_by_type())
    }), 200

# ─── GET /admin/queue/<event_id> ─────────────────────────────────────────────
@admin_bp.route("/admin/queue/<event_id>", methods=["GET"])
def view_queue(event_id):
    queue = rs.get_full_queue(event_id)
    length = rs.get_queue_length(event_id)
    return jsonify({
        "event_id": event_id,
        "queue_length": length,
        "queue": queue
    }), 200

# ─── POST /admin/queue/<event_id>/process ────────────────────────────────────
@admin_bp.route("/admin/queue/<event_id>/process", methods=["POST"])
def process_queue(event_id):
    """LPOP one student from the queue (FIFO worker simulation)."""
    student_id = rs.dequeue_registration(event_id)
    if not student_id:
        return jsonify({"message": "Queue is empty"}), 200
    return jsonify({"processed_student_id": student_id}), 200

# ─── POST /admin/attendance ──────────────────────────────────────────────────
@admin_bp.route("/admin/attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()
    event_id   = data.get("event_id")
    student_id = data.get("student_id")
    attended   = data.get("attended", True)
    if not event_id or not student_id:
        return jsonify({"error": "event_id and student_id required"}), 400
    ms.mark_attendance(event_id, student_id, attended)
    return jsonify({"message": "Attendance updated"}), 200

# ─── GET /admin/students ─────────────────────────────────────────────────────
@admin_bp.route("/admin/students", methods=["GET"])
def list_students():
    students = ms.get_all_students()
    return jsonify(serialize(students)), 200

# ─── GET /admin/registrations/<event_id> ────────────────────────────────────
@admin_bp.route("/admin/registrations/<event_id>", methods=["GET"])
def list_registrations(event_id):
    regs = ms.get_registrations_for_event(event_id)
    return jsonify(serialize(regs)), 200
