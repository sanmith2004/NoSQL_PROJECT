import redis
from config import Config

_redis_client = None

def get_redis():
    """Return Redis client (singleton). Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is None:
        try:
            client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2
            )
            client.ping()
            _redis_client = client
        except Exception as e:
            print(f"[Redis] Connection failed: {e}")
            return None
    return _redis_client

# ─── Seat Counter ────────────────────────────────────────────────────────────

def init_seat_counter(event_id: str, max_seats: int):
    r = get_redis()
    if r:
        r.set(f"seats:{event_id}", max_seats)

def get_available_seats(event_id: str):
    r = get_redis()
    if r:
        val = r.get(f"seats:{event_id}")
        return int(val) if val is not None else None
    return None

def decrement_seat(event_id: str):
    """
    Atomically decrement seat counter.
    Returns (success: bool, remaining: int)
    """
    r = get_redis()
    if not r:
        return None, None
    remaining = r.decr(f"seats:{event_id}")
    if remaining < 0:
        r.incr(f"seats:{event_id}")   # rollback
        return False, 0
    return True, remaining

def increment_seat(event_id: str):
    """Increment seat counter on cancellation."""
    r = get_redis()
    if r:
        return int(r.incr(f"seats:{event_id}"))
    return None

# ─── Registration Queue ───────────────────────────────────────────────────────

def enqueue_registration(event_id: str, student_id: str):
    r = get_redis()
    if r:
        r.rpush(f"regqueue:{event_id}", student_id)

def dequeue_registration(event_id: str):
    r = get_redis()
    if r:
        return r.lpop(f"regqueue:{event_id}")
    return None

def get_queue_length(event_id: str):
    r = get_redis()
    if r:
        return r.llen(f"regqueue:{event_id}")
    return 0

def get_full_queue(event_id: str):
    r = get_redis()
    if r:
        return r.lrange(f"regqueue:{event_id}", 0, -1)
    return []

# ─── Countdown TTL ────────────────────────────────────────────────────────────

def set_event_countdown(event_id: str, seconds_until_event: int):
    r = get_redis()
    if r and seconds_until_event > 0:
        r.set(f"countdown:{event_id}", seconds_until_event, ex=seconds_until_event)

def get_event_countdown(event_id: str):
    r = get_redis()
    if r:
        ttl = r.ttl(f"countdown:{event_id}")
        return ttl if ttl > 0 else 0
    return None

# ─── Pub/Sub Publish ──────────────────────────────────────────────────────────

def publish(channel: str, message: str):
    r = get_redis()
    if r:
        r.publish(channel, message)
