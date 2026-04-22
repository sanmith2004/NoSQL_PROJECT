import json
import threading
from flask import Blueprint, Response, stream_with_context
from services.redis_service import get_redis

notif_bp = Blueprint("notifications", __name__)

CHANNELS = ["events:new", "events:almostfull", "events:seatopen", "events:cancelled"]

@notif_bp.route("/notifications/stream", methods=["GET"])
def sse_stream():
    """
    Server-Sent Events endpoint.
    Subscribes to all Redis pub/sub channels and streams messages to the browser.
    """
    def generate():
        r = get_redis()
        if not r:
            yield "data: {\"error\": \"Redis unavailable\"}\n\n"
            return

        pubsub = r.pubsub()
        pubsub.subscribe(*CHANNELS)

        yield "data: {\"type\": \"connected\", \"message\": \"Notification stream active\"}\n\n"

        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
        except GeneratorExit:
            pubsub.unsubscribe()
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
        finally:
            pubsub.close()

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )
