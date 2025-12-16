from typing import List
from datetime import datetime
from model.model import HistoryRecord
from MetricRepositoryInterface import MetricRepositoryInterface


class MetricRepositoryImpl(MetricRepositoryInterface):
    """
    MongoDB-based implementation of MetricRepository.
    """

    def __init__(self, db, collection_name: str):
        self.collection = db[collection_name]

    async def get_latest(self, limit: int = 100) -> List[HistoryRecord]:
        cursor = (
            self.collection
            .find()
            .sort("timestamp", -1)
            .limit(limit)
        )

        results: List[HistoryRecord] = []
        async for doc in cursor:
            results.append(self._to_model(doc))

        return results

    async def get_by_time_range(
        self,
        start: datetime,
        end: datetime,
    ) -> List[HistoryRecord]:
        cursor = (
            self.collection
            .find({
                "timestamp": {
                    "$gte": start,
                    "$lte": end,
                }
            })
            .sort("timestamp", 1)
        )

        results: List[HistoryRecord] = []
        async for doc in cursor:
            results.append(self._to_model(doc))

        return results

    def _to_model(self, doc: dict) -> HistoryRecord:
        """
        Internal mapper: Mongo document -> Pydantic model.
        """
        return HistoryRecord(
            id=str(doc["_id"]),
            metric=doc["metric"],
            value=doc["value"],
            timestamp=doc["timestamp"],
            timestamp_local=doc.get("timestamp_local"),
        )