import json
import redis.asyncio as aioredis
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger


async def publish_run_event(
    run_id: str,
    event_type: str,
    payload: Dict[str, Any],
    redis_url: Optional[str] = None,
) -> None:
    """
    Publishes an atomic research event to Redis Pub/Sub channel 'research_run:{run_id}' (§18, §23).
    """
    url = redis_url or settings.REDIS_URL
    channel = f"research_run:{run_id}"

    event_message = {
        "event": event_type,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }

    try:
        client = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
        await client.publish(channel, json.dumps(event_message))
        await client.aclose()
    except Exception as e:
        logger.warning(f"Failed to publish event to Redis channel {channel}: {e}")
