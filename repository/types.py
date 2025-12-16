# repositories/types.py
from typing import TypedDict, Literal

class UserAuthRecord(TypedDict):
    id:str 
    email: str
    password_hash: str
    role: Literal["admin", "user"]