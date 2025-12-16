# repositories/device_repository.py
from abc import ABC, abstractmethod
from typing import List
from persistence.model import Device
from persistence.model import HistoryDataItem

class DeviceRepository(ABC):

    @abstractmethod
    def get_by_id(self, device_id: int) -> Device | None:
        pass

    @abstractmethod
    def list_by_owner(self, owner_id: int) -> List[Device]:
        pass

    @abstractmethod
    def create(self, device: Device) -> Device:
        pass

    @abstractmethod
    def delete(self, device_id: int) -> None:
        pass

    @abstractmethod
    def get_history(
        self,
        device_id: int,
        time_filter: str,
    ) -> List[HistoryDataItem]:
        pass

    @abstractmethod
    def update_history_value(
        self,
        row_id: str,
        value: float,
    ) -> None:
        pass