from bson import ObjectId
from datetime import datetime
from database import get_db

# ─── Events ──────────────────────────────────────────────────────────────────

def create_event(data: dict) -> dict:
    db = get_db()
    data["registered_count"] = 0
    data["created_at"] = datetime.utcnow()
    result = db.events.insert_one(data)
    data["_id"] = result.inserted_id
    return data

def get_all_events(filters: dict = None) -> list:
    db = get_db()
    query = filters or {}
    events = list(db.events.find(query).sort("date", 1))
    for e in events:
        e["_id"] = str(e["_id"])
    return events

def get_event_by_id(event_id: str) -> dict | None:
    db = get_db()
    try:
        event = db.events.find_one({"_id": ObjectId(event_id)})
        if event:
            event["_id"] = str(event["_id"])
        return event
    except Exception:
        return None

def increment_registered_count(event_id: str):
    """Computed Pattern: use $inc to maintain registered_count."""
    db = get_db()
    db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$inc": {"registered_count": 1}}
    )

def decrement_registered_count(event_id: str):
    db = get_db()
    db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$inc": {"registered_count": -1}}
    )

# ─── Registrations ───────────────────────────────────────────────────────────

def create_registration(event_id: str, student_id: str) -> dict:
    db = get_db()
    reg = {
        "event_id": ObjectId(event_id),
        "student_id": ObjectId(student_id),
        "timestamp": datetime.utcnow(),
        "attended": False
    }
    result = db.registrations.insert_one(reg)
    reg["_id"] = str(result.inserted_id)
    reg["event_id"] = event_id
    reg["student_id"] = student_id
    return reg

def delete_registration(event_id: str, student_id: str) -> bool:
    db = get_db()
    result = db.registrations.delete_one({
        "event_id": ObjectId(event_id),
        "student_id": ObjectId(student_id)
    })
    return result.deleted_count > 0

def get_registration(event_id: str, student_id: str) -> dict | None:
    db = get_db()
    reg = db.registrations.find_one({
        "event_id": ObjectId(event_id),
        "student_id": ObjectId(student_id)
    })
    if reg:
        reg["_id"] = str(reg["_id"])
        reg["event_id"] = str(reg["event_id"])
        reg["student_id"] = str(reg["student_id"])
    return reg

def get_registrations_for_event(event_id: str) -> list:
    db = get_db()
    regs = list(db.registrations.find({"event_id": ObjectId(event_id)}))
    for r in regs:
        r["_id"] = str(r["_id"])
        r["event_id"] = str(r["event_id"])
        r["student_id"] = str(r["student_id"])
    return regs

def mark_attendance(event_id: str, student_id: str, attended: bool):
    db = get_db()
    db.registrations.update_one(
        {"event_id": ObjectId(event_id), "student_id": ObjectId(student_id)},
        {"$set": {"attended": attended}}
    )

# ─── Students ────────────────────────────────────────────────────────────────

def get_or_create_student(name: str, email: str, department: str) -> dict:
    db = get_db()
    student = db.students.find_one({"email": email})
    if not student:
        doc = {"name": name, "email": email, "department": department,
               "created_at": datetime.utcnow()}
        result = db.students.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc
    student["_id"] = str(student["_id"])
    return student

def get_student_by_id(student_id: str) -> dict | None:
    db = get_db()
    try:
        s = db.students.find_one({"_id": ObjectId(student_id)})
        if s:
            s["_id"] = str(s["_id"])
        return s
    except Exception:
        return None

def get_all_students() -> list:
    db = get_db()
    students = list(db.students.find())
    for s in students:
        s["_id"] = str(s["_id"])
    return students

# ─── Analytics Aggregations ──────────────────────────────────────────────────

def agg_highest_registrations(limit: int = 5) -> list:
    db = get_db()
    pipeline = [
        {"$sort": {"registered_count": -1}},
        {"$limit": limit},
        {"$project": {"title": 1, "type": 1, "registered_count": 1, "max_seats": 1}}
    ]
    return list(db.events.aggregate(pipeline))

def agg_dept_participation() -> list:
    db = get_db()
    pipeline = [
        {"$lookup": {
            "from": "students",
            "localField": "student_id",
            "foreignField": "_id",
            "as": "student"
        }},
        {"$unwind": "$student"},
        {"$group": {
            "_id": "$student.department",
            "total_registrations": {"$sum": 1},
            "unique_students": {"$addToSet": "$student_id"}
        }},
        {"$project": {
            "department": "$_id",
            "total_registrations": 1,
            "unique_students": {"$size": "$unique_students"}
        }},
        {"$sort": {"total_registrations": -1}}
    ]
    return list(db.registrations.aggregate(pipeline))

def agg_most_active_students(limit: int = 5) -> list:
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$student_id",
            "events_registered": {"$sum": 1},
            "events_attended": {"$sum": {"$cond": ["$attended", 1, 0]}}
        }},
        {"$sort": {"events_registered": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "students",
            "localField": "_id",
            "foreignField": "_id",
            "as": "student"
        }},
        {"$unwind": "$student"},
        {"$project": {
            "name": "$student.name",
            "department": "$student.department",
            "events_registered": 1,
            "events_attended": 1
        }}
    ]
    return list(db.registrations.aggregate(pipeline))

def agg_attendance_rate_by_type() -> list:
    db = get_db()
    pipeline = [
        {"$lookup": {
            "from": "events",
            "localField": "event_id",
            "foreignField": "_id",
            "as": "event"
        }},
        {"$unwind": "$event"},
        {"$group": {
            "_id": "$event.type",
            "total": {"$sum": 1},
            "attended": {"$sum": {"$cond": ["$attended", 1, 0]}}
        }},
        {"$project": {
            "event_type": "$_id",
            "total_registrations": "$total",
            "total_attended": "$attended",
            "attendance_rate": {
                "$round": [
                    {"$multiply": [
                        {"$divide": ["$attended", {"$max": ["$total", 1]}]},
                        100
                    ]}, 2
                ]
            }
        }},
        {"$sort": {"attendance_rate": -1}}
    ]
    return list(db.registrations.aggregate(pipeline))
