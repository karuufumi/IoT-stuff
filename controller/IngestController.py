# controller/IngestController.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
from data.mongo import mongo
from realtime.connection_manager import manager

router = APIRouter(prefix="/ingest", tags=["Ingest"])

@router.post("/")
async def ingest(metric: str, value: float):
    if mongo.client is None:
        raise RuntimeError("MongoDB client not initialized")

    if not metric:
        raise HTTPException(status_code=400, detail="Metric is required")

    ts = datetime.utcnow()

    collection = mongo.client["IoT_"][metric]

    await collection.insert_one({
        "value": value,
        "timestamp": ts,
    })

    await manager.broadcast({
        "metric": metric,
        "value": value,
        "timestamp": ts.isoformat(),
    })

    return {"status": "ok"}