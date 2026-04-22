from pymongo import MongoClient, ASCENDING
from config import Config

_mongo_client = None
_db = None

def get_db():
    """Return the MongoDB database instance (singleton)."""
    global _mongo_client, _db
    if _db is None:
        _mongo_client = MongoClient(Config.MONGO_URI)
        _db = _mongo_client[Config.DB_NAME]
        _ensure_indexes(_db)
    return _db

def _ensure_indexes(db):
    """Create all required indexes."""
    # Compound index on attributes array (Attribute Pattern)
    db.events.create_index(
        [("attributes.key", ASCENDING), ("attributes.value", ASCENDING)],
        name="idx_attributes_key_value"
    )
    # Index for fast event lookup by type
    db.events.create_index([("type", ASCENDING)], name="idx_event_type")
    # Index for registrations by event
    db.registrations.create_index([("event_id", ASCENDING)], name="idx_reg_event")
    # Index for registrations by student
    db.registrations.create_index([("student_id", ASCENDING)], name="idx_reg_student")
    # Compound unique: one registration per student per event
    db.registrations.create_index(
        [("event_id", ASCENDING), ("student_id", ASCENDING)],
        unique=True,
        name="idx_reg_unique"
    )
    # Students index
    db.students.create_index([("email", ASCENDING)], unique=True, name="idx_student_email")
