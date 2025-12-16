# controller/HistoryController.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from service.HistoryService import HistoryService
from repository.HistoryRepositoryImpl import HistoryRepositoryImpl
from dependencies.auth import get_current_user

router = APIRouter(prefix="/history", tags=["History"])

def get_history_service():
    return HistoryService(HistoryRepositoryImpl())


@router.get("/{metric}")
async def get_history(
    metric: str,  # lux | rh | rt
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    user = Depends(get_current_user),
    service: HistoryService = Depends(get_history_service),
):
    if metric not in {"lux", "rh", "rt"}:
        raise HTTPException(status_code=404, detail="Unknown metric")

    return await service.get_metric_history(metric, start, end, limit)