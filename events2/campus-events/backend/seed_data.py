"""
Seed script: inserts 10+ events (4 types) + sample students + registrations.
Run: python seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone, timedelta
from database import get_db
from services.redis_service import init_seat_counter, set_event_countdown
from utils.helpers import seconds_until

db = get_db()

# ── Clear existing data ──────────────────────────────────────────────────────
db.events.drop()
db.registrations.drop()
db.students.drop()
print("Cleared existing collections.")

# ── Helper ───────────────────────────────────────────────────────────────────
def future(days):
    return datetime.now(timezone.utc) + timedelta(days=days)

# ── Events (Attribute Pattern) ───────────────────────────────────────────────
events_data = [
    # ── Workshops ──
    {
        "title": "Python for Data Science",
        "type": "workshop",
        "date": future(5),
        "venue": "Lab 101",
        "max_seats": 30,
        "registered_count": 0,
        "attributes": [
            {"key": "prerequisites", "value": "Basic Python"},
            {"key": "duration",      "value": "3 hours"},
            {"key": "tools",         "value": "Jupyter, Pandas, NumPy"}
        ]
    },
    {
        "title": "Web Development Bootcamp",
        "type": "workshop",
        "date": future(8),
        "venue": "Lab 202",
        "max_seats": 25,
        "registered_count": 0,
        "attributes": [
            {"key": "prerequisites", "value": "HTML basics"},
            {"key": "duration",      "value": "6 hours"},
            {"key": "tools",         "value": "React, Node.js"}
        ]
    },
    {
        "title": "Machine Learning Fundamentals",
        "type": "workshop",
        "date": future(12),
        "venue": "Seminar Hall A",
        "max_seats": 40,
        "registered_count": 0,
        "attributes": [
            {"key": "prerequisites", "value": "Python, Statistics"},
            {"key": "duration",      "value": "4 hours"},
            {"key": "tools",         "value": "scikit-learn, TensorFlow"}
        ]
    },
    # ── Hackathons ──
    {
        "title": "Smart Campus Hackathon",
        "type": "hackathon",
        "date": future(15),
        "venue": "Main Auditorium",
        "max_seats": 100,
        "registered_count": 0,
        "attributes": [
            {"key": "team_size",  "value": "2-4"},
            {"key": "prize_pool", "value": "₹50,000"},
            {"key": "theme",      "value": "IoT & Smart Infrastructure"}
        ]
    },
    {
        "title": "AI Innovation Challenge",
        "type": "hackathon",
        "date": future(20),
        "venue": "Innovation Hub",
        "max_seats": 80,
        "registered_count": 0,
        "attributes": [
            {"key": "team_size",  "value": "3-5"},
            {"key": "prize_pool", "value": "₹1,00,000"},
            {"key": "theme",      "value": "Generative AI Solutions"}
        ]
    },
    {
        "title": "Green Tech Hackathon",
        "type": "hackathon",
        "date": future(25),
        "venue": "Engineering Block",
        "max_seats": 60,
        "registered_count": 0,
        "attributes": [
            {"key": "team_size",  "value": "2-3"},
            {"key": "prize_pool", "value": "₹30,000"},
            {"key": "theme",      "value": "Sustainability & Clean Energy"}
        ]
    },
    # ── Seminars ──
    {
        "title": "Cybersecurity in the Modern Era",
        "type": "seminar",
        "date": future(3),
        "venue": "Seminar Hall B",
        "max_seats": 150,
        "registered_count": 0,
        "attributes": [
            {"key": "speaker",   "value": "Dr. Priya Sharma, IIT Delhi"},
            {"key": "recording", "value": "Yes"},
            {"key": "topic",     "value": "Zero Trust Architecture"}
        ]
    },
    {
        "title": "Cloud Computing Trends 2025",
        "type": "seminar",
        "date": future(7),
        "venue": "Conference Room 1",
        "max_seats": 80,
        "registered_count": 0,
        "attributes": [
            {"key": "speaker",   "value": "Mr. Arjun Mehta, AWS India"},
            {"key": "recording", "value": "Yes"},
            {"key": "topic",     "value": "Serverless & Edge Computing"}
        ]
    },
    # ── Guest Lectures ──
    {
        "title": "Career in Product Management",
        "type": "guest_lecture",
        "date": future(4),
        "venue": "Auditorium B",
        "max_seats": 200,
        "registered_count": 0,
        "attributes": [
            {"key": "speaker",      "value": "Ms. Neha Gupta, Google"},
            {"key": "industry",     "value": "Tech / Product"},
            {"key": "registration", "value": "Open"}
        ]
    },
    {
        "title": "Entrepreneurship & Startups",
        "type": "guest_lecture",
        "date": future(10),
        "venue": "Main Auditorium",
        "max_seats": 300,
        "registered_count": 0,
        "attributes": [
            {"key": "speaker",  "value": "Mr. Rahul Verma, Founder Zomato"},
            {"key": "industry", "value": "Startup Ecosystem"},
            {"key": "qa",       "value": "Yes"}
        ]
    },
    {
        "title": "Open Source Contribution Guide",
        "type": "guest_lecture",
        "date": future(18),
        "venue": "Lab 303",
        "max_seats": 50,
        "registered_count": 0,
        "attributes": [
            {"key": "speaker",  "value": "Mr. Kiran Rao, GitHub"},
            {"key": "industry", "value": "Open Source"},
            {"key": "hands_on", "value": "Yes"}
        ]
    }
]

inserted_events = db.events.insert_many(events_data)
event_ids = [str(eid) for eid in inserted_events.inserted_ids]
print(f"Inserted {len(event_ids)} events.")

# Init Redis counters & countdowns
for i, eid in enumerate(event_ids):
    max_seats = events_data[i]["max_seats"]
    init_seat_counter(eid, max_seats)
    secs = seconds_until(events_data[i]["date"])
    set_event_countdown(eid, secs)
print("Redis seat counters and countdowns initialized.")

# ── Sample Students ──────────────────────────────────────────────────────────
students_data = [
    {"name": "Aarav Patel",    "email": "aarav@college.edu",    "department": "CSE"},
    {"name": "Priya Singh",    "email": "priya@college.edu",    "department": "ECE"},
    {"name": "Rohan Sharma",   "email": "rohan@college.edu",    "department": "ME"},
    {"name": "Sneha Reddy",    "email": "sneha@college.edu",    "department": "CSE"},
    {"name": "Vikram Nair",    "email": "vikram@college.edu",   "department": "IT"},
    {"name": "Ananya Iyer",    "email": "ananya@college.edu",   "department": "CSE"},
    {"name": "Karthik Menon",  "email": "karthik@college.edu",  "department": "EEE"},
    {"name": "Divya Krishnan", "email": "divya@college.edu",    "department": "CSE"},
    {"name": "Arjun Das",      "email": "arjun@college.edu",    "department": "IT"},
    {"name": "Meera Joshi",    "email": "meera@college.edu",    "department": "ME"},
]
inserted_students = db.students.insert_many(students_data)
student_ids = [str(sid) for sid in inserted_students.inserted_ids]
print(f"Inserted {len(student_ids)} students.")

# ── Sample Registrations ─────────────────────────────────────────────────────
from bson import ObjectId
from datetime import datetime as dt

registrations = []
# First 3 students register for event 0 (Python workshop)
for i in range(3):
    registrations.append({
        "event_id":   ObjectId(event_ids[0]),
        "student_id": ObjectId(student_ids[i]),
        "timestamp":  dt.utcnow(),
        "attended":   False
    })
    db.events.update_one({"_id": ObjectId(event_ids[0])}, {"$inc": {"registered_count": 1}})

# Students 3-6 register for hackathon (event 3)
for i in range(3, 7):
    registrations.append({
        "event_id":   ObjectId(event_ids[3]),
        "student_id": ObjectId(student_ids[i]),
        "timestamp":  dt.utcnow(),
        "attended":   False
    })
    db.events.update_one({"_id": ObjectId(event_ids[3])}, {"$inc": {"registered_count": 1}})

# All students register for seminar (event 6)
for i in range(len(student_ids)):
    registrations.append({
        "event_id":   ObjectId(event_ids[6]),
        "student_id": ObjectId(student_ids[i]),
        "timestamp":  dt.utcnow(),
        "attended":   i < 7   # first 7 attended
    })
    db.events.update_one({"_id": ObjectId(event_ids[6])}, {"$inc": {"registered_count": 1}})

if registrations:
    db.registrations.insert_many(registrations)
    print(f"Inserted {len(registrations)} registrations.")

# Sync Redis seat counters with actual registrations
for i, eid in enumerate(event_ids):
    event = db.events.find_one({"_id": ObjectId(eid)})
    actual_available = event["max_seats"] - event["registered_count"]
    init_seat_counter(eid, actual_available)

print("\n✅ Seed complete! Database: my_events")
print(f"   Events: {len(event_ids)} | Students: {len(student_ids)} | Registrations: {len(registrations)}")
