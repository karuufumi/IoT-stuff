from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from model.model import HistoryRecord  


class MetricRepositoryInterface(ABC):
    """
    Interface for metric (time-series) persistence.
    """

    @abstractmethod
    async def get_latest(self, limit: int) -> List[HistoryRecord]:
        pass

    @abstractmethod
    async def get_by_time_range(
        self,
        start: datetime,
        end: datetime,
    ) -> List[HistoryRecord]:
        pass