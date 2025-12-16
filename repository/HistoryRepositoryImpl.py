# repository/HistoryRepositoryImpl.py
from datetime import datetime
from data.mongo import mongo
from model.model import HistoryRecord
from repository.HistoryRepositoryInterface import HistoryRepositoryInterface


class HistoryRepositoryImpl(HistoryRepositoryInterface):

    async def get_history(
        self,
        metric: str,
        start: datetime | None,
        end: datetime | None,
        limit: int = 100,
    ):
        if mongo.client is None:
            raise RuntimeError("MongoDB client not initialized")

        collection = mongo.client["IoT_"][metric]

        query: dict = {}
        if start or end:
            query["timestamp"] = {}
            if start:
                query["timestamp"]["$gte"] = start
            if end:
                query["timestamp"]["$lte"] = end

        cursor = (
            collection
            .find(query)
            .sort("timestamp", -1)
            .limit(limit)
        )

        results = []

        async for doc in cursor:
            # 🔑 FIX HERE
            timestamp_local = None
            raw = doc.get("timestamp_local")

            if isinstance(raw, datetime):
                timestamp_local = raw
            elif isinstance(raw, str):
                timestamp_local = datetime.fromisoformat(raw)

            results.append(
                HistoryRecord(
                    id=str(doc["_id"]),
                    metric=metric,
                    value=float(doc["value"]),
                    timestamp=doc["timestamp"]
                    if isinstance(doc["timestamp"], datetime)
                    else datetime.fromisoformat(
                        doc["timestamp"].replace("Z", "+00:00")
                    ),
                    timestamp_local=timestamp_local,
                )
            )

        return results