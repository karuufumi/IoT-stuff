import asyncio
import os
import httpx
from datetime import datetime
from typing import Optional, Tuple, List
from datetime import timezone
import traceback

from data.mongo import mongo
from realtime.connection_manager import manager

# ======================
# Environment variables
# ======================

ADAFRUIT_USERNAME = os.getenv("ADAFRUIT_USERNAME")
ADAFRUIT_KEY = os.getenv("ADAFRUIT_KEY")
ADAFRUIT_FEEDS = os.getenv("ADAFRUIT_FEEDS", "").split(",")
GATEWAY_INTERVAL = int(os.getenv("ADAFRUIT_POLL_INTERVAL", "3"))

BASE_URL = "https://io.adafruit.com/api/v2"

if not ADAFRUIT_USERNAME:
    raise RuntimeError("ADAFRUIT_USERNAME is not set")

if not ADAFRUIT_KEY:
    raise RuntimeError("ADAFRUIT_KEY is not set")

if not ADAFRUIT_FEEDS or ADAFRUIT_FEEDS == [""]:
    raise RuntimeError("ADAFRUIT_FEEDS is not set")


# ======================
# Adafruit API access
# ======================

async def fetch_latest(feed: str) -> Optional[dict]:
    url = f"{BASE_URL}/{ADAFRUIT_USERNAME}/feeds/{feed}/data/last"
    headers = {"X-AIO-Key": ADAFRUIT_KEY}

    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(url, headers=headers) # type: ignore

    if response.status_code != 200:
        print(f"⚠️ Adafruit HTTP {response.status_code} for feed '{feed}'")
        return None

    try:
        return response.json()
    except Exception:
        print(f"⚠️ Invalid JSON for feed '{feed}'")
        return None


# ======================
# Ingest state helpers
# ======================

async def get_last_timestamp(metric: str) -> Optional[datetime]:
    state = await mongo.client["IoT_"]["ingest_state"].find_one(  # type: ignore
        {"metric": metric}
    )
    if not state:
        return None
    return state.get("last_timestamp")

def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware in UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

async def update_last_timestamp(metric: str, timestamp: datetime) -> None:
    await mongo.client["IoT_"]["ingest_state"].update_one(  # type: ignore
        {"metric": metric},
        {"$set": {"last_timestamp": timestamp}},
        upsert=True,
    )


# ======================
# Core processing logic
# ======================

async def process_feed(
    metric: str,
) -> Optional[Tuple[str, float, datetime]]:
    """
    Returns (metric, value, timestamp) if data exists (new or duplicate),
    otherwise None.
    """

    data = await fetch_latest(metric)
    if not data:
        return None

    try:
        value = float(data["value"])
        timestamp = datetime.fromisoformat(
            data["created_at"].replace("Z", "+00:00")
        )
    except (KeyError, ValueError):
        return None

    last_ts = await get_last_timestamp(metric)

    timestamp = ensure_utc(timestamp)

    if last_ts:
        last_ts = ensure_utc(last_ts)
        if timestamp <= last_ts:
            return metric, value, timestamp

    # Persist
    await mongo.client["IoT_"][metric].insert_one(  # type: ignore
        {
            "value": value,
            "timestamp": timestamp,
        }
    )

    await update_last_timestamp(metric, timestamp)

    await manager.broadcast(
        {
            "metric": metric,
            "value": value,
            "timestamp": timestamp.isoformat(),
        }
    )

    return metric, value, timestamp


# ======================
# Gateway main loop
# ======================

async def start_adafruit_gateway() -> None:
    print("🌉 Adafruit gateway started")

    while True:
        try:
            if mongo.client is None:
                await asyncio.sleep(GATEWAY_INTERVAL)
                continue

            results: List[Tuple[str, float, datetime]] = []

            for metric in [m.strip() for m in ADAFRUIT_FEEDS if m.strip()]:
                result = await process_feed(metric)
                if result:
                    results.append(result)

            if results:
                print("📊 Gateway snapshot:")
                for metric, value, ts in results:
                    print(f"  • {metric:<3} = {value} @ {ts.isoformat()}")

        except asyncio.CancelledError:
            print("🛑 Adafruit gateway stopped")
            break

        except Exception as e:
            print("⚠️ Gateway error:", repr(e))
            traceback.print_exc()

        await asyncio.sleep(GATEWAY_INTERVAL)