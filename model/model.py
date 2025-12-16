from typing import Union, Literal
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional

from datetime import datetime



class Account(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Password must be 8–72 characters"
    )

class User(BaseModel):
    id: str
    email: EmailStr
    role: Literal["admin", "user"]


class Metric(str, Enum):
    Temperature = "Temperature"
    Humidity = "Humidity"
    Light = "Light"


class Device(BaseModel):
    id: int
    name: str
    ownerId: int


class Row(BaseModel):
    id: str
    device: str                 # device name (mock-friendly)
    sensor: str
    value: Union[int, float, str]  # numeric sensors + PIR states
    date: datetime              # ISO string → datetime
    ts: int                     # timestamp (ms)


class HistoryRecord(BaseModel):
    id: str
    metric: str
    value: float
    timestamp: datetime
    timestamp_local: Optional[datetime] = None