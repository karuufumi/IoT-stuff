from typing import Literal
from model.model import Account, User
from repository.UserRepositoryInterface import UserRepositoryInterface
from helper.password import hash_password, verify_password
from helper.jwt import create_access_token, create_refresh_token


Role = Literal["admin", "user"]


class AuthService:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    async def register(self, account: Account) -> User:
        existing = await self.user_repo.find_by_email(account.email)
        if existing:
            raise ValueError("Email already registered")

        password_hash = (account.password)

        return await self.user_repo.create(
            email=account.email,
            password_hash=password_hash,
            role="user",
        )

    async def login(self, account: Account) -> dict:
        record = await self.user_repo.find_by_email(account.email)
        if not record:
            raise ValueError("Invalid credentials")

        if not verify_password(account.password, record["password_hash"]):
            raise ValueError("Invalid credentials")

        access_token = create_access_token(
            user_id=record["id"],
            role=record["role"],
        )

        

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": record["id"],
                "email": record["email"],
                "role": record["role"],
            },
        }