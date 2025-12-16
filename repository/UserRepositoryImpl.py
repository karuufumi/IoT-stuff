from typing import Literal
from bson import ObjectId
from model.model import User
from repository.UserRepositoryInterface import UserRepositoryInterface
from repository.types import UserAuthRecord
from data.mongo import mongo


class UserRepositoryImpl(UserRepositoryInterface):
    def __init__(self):
        if not mongo.client:
            raise RuntimeError("MongoDB client not initialized")

        self.collection = mongo.client["IoT_"]["User"]

    async def find_by_id(self, user_id: str) -> User | None:
        doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        if not doc:
            return None

        return User(
            id=str(doc["_id"]),
            email=doc["email"],
            role=doc["role"],
        )

    async def find_by_email(self, email: str) -> UserAuthRecord | None:
        doc = await self.collection.find_one({"email": email})
        if not doc:
            return None

        return {
            "id": str(doc["_id"]),
            "email": doc["email"],
            "password_hash": doc["password"],
            "role": doc["role"],
        }

    async def create(
        self,
        email: str,
        password_hash: str,
        role: Literal["admin", "user"],
    ) -> User:
        result = await self.collection.insert_one({
            "email": email,
            "password": password_hash,
            "role": role,
            "isVerified": True,
        })

        return User(
            id=str(result.inserted_id),
            email=email,
            role=role,
        )

    async def update_password(self, user_id: str, password_hash: str) -> None:
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": password_hash}},
        )

        if result.matched_count == 0:
            raise ValueError("User not found")