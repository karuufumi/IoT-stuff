# repository/HistoryRepositoryInterface.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from model.model import HistoryRecord
class HistoryRepositoryInterface(ABC):

    @abstractmethod
    async def get_history(
        self,
        metric: str,
        start: datetime | None,
        end: datetime | None,
        limit: int = 100,
    ) -> List[HistoryRecord]:
        ...