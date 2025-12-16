# service/HistoryService.py
from repository.HistoryRepositoryInterface import HistoryRepositoryInterface

class HistoryService:
    def __init__(self, repo: HistoryRepositoryInterface):
        self.repo = repo

    async def get_metric_history(
        self,
        metric: str,
        start=None,
        end=None,
        limit: int = 100,
    ):
        return await self.repo.get_history(metric, start, end, limit)