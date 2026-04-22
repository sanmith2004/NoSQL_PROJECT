# Campus Event Management & Notification System

## Stack
- **Backend**: Python / Flask
- **Database**: MongoDB (`my_events`)
- **Real-time**: Redis (seats, queue, pub/sub, countdown)
- **Frontend**: HTML + CSS + Vanilla JS

## Quick Start

### 1. Install dependencies
```bash
cd campus-events/backend
pip install -r requirements.txt
```

### 2. Make sure MongoDB and Redis are running
```bash
# MongoDB (default port 27017)
mongod

# Redis (default port 6379)
redis-server
```

### 3. Seed the database (10+ events, students, registrations)
```bash
cd campus-events/backend
python seed_data.py
```

### 4. Start the server
```bash
cd campus-events/backend
python app.py
```

Open **http://localhost:5000** in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/events` | List all events (with live seats & countdown) |
| GET | `/events/<id>` | Get single event |
| POST | `/events` | Create event (admin) |
| POST | `/events/<id>/register` | Register student |
| DELETE | `/events/<id>/register` | Cancel registration |
| GET | `/events/<id>/seats` | Live seat count (Redis → MongoDB fallback) |
| GET | `/dashboard` | Summary stats |
| GET | `/admin/analytics` | Aggregation reports |
| GET | `/admin/queue/<id>` | View registration queue |
| POST | `/admin/queue/<id>/process` | LPOP from queue |
| POST | `/admin/attendance` | Mark attendance |
| GET | `/notifications/stream` | SSE pub/sub stream |
| GET | `/health` | Redis + MongoDB health check |

---

## MongoDB Schema Design

### Events — Attribute Pattern
```json
{
  "title": "Python for Data Science",
  "type": "workshop",
  "date": "ISODate",
  "venue": "Lab 101",
  "max_seats": 30,
  "registered_count": 0,
  "attributes": [
    { "key": "prerequisites", "value": "Basic Python" },
    { "key": "duration",      "value": "3 hours" }
  ]
}
```
**Why Attribute Pattern?** Each event type (workshop/hackathon/seminar/guest_lecture) has different metadata. Storing them as `[{key, value}]` avoids sparse fields and allows a single compound index `{attributes.key:1, attributes.value:1}` to query any attribute efficiently.

### Registrations — Reference Pattern
```json
{
  "event_id": "ObjectId",
  "student_id": "ObjectId",
  "timestamp": "ISODate",
  "attended": false
}
```

### Computed Pattern
`registered_count` is maintained via `$inc` on every register/cancel — avoids expensive `COUNT` aggregations on hot reads.

### Indexes
- `{attributes.key:1, attributes.value:1}` — compound index for attribute queries
- `{event_id:1, student_id:1}` unique — prevents duplicate registrations
- `{type:1}` — fast filter by event type
- `{email:1}` unique on students

---

## Redis Design

| Key | Type | Purpose |
|-----|------|---------|
| `seats:<eventId>` | String | Available seat counter (DECR/INCR) |
| `regqueue:<eventId>` | List | FIFO registration queue (RPUSH/LPOP) |
| `countdown:<eventId>` | String+TTL | Seconds until event (TTL = countdown) |

### Pub/Sub Channels
| Channel | Trigger |
|---------|---------|
| `events:new` | New event created |
| `events:almostfull` | Seats drop below 5 |
| `events:seatopen` | Registration cancelled |

### Concurrency Protection
`DECR seats:<id>` is atomic. If result < 0, immediately `INCR` back and reject — prevents overbooking even under concurrent requests.

---

## Fallback
If Redis is down, `/events/<id>/seats` returns `registered_count` from MongoDB with `"source": "mongodb_fallback"`.
