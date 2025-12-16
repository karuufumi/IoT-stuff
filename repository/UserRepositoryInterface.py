from abc import ABC, abstractmethod
from typing import Literal
from model.model import User
from repository.types import UserAuthRecord

class UserRepositoryInterface(ABC):

    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None:
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> UserAuthRecord | None:
        ...

    @abstractmethod
    async def create(
        self,
        email: str,
        password_hash: str,
        role: Literal["admin", "user"],
    ) -> User:
        ...

    @abstractmethod
    async def update_password(self, user_id: str, password_hash: str) -> None:
        ...