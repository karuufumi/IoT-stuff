from pymongo import AsyncMongoClient
from typing import Optional

class MongoDB:
    client: Optional[AsyncMongoClient] = None

mongo = MongoDB()