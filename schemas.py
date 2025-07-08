from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import datetime

class Person_scheme(BaseModel):
    name: str
    surname: str
    email: str
    created_at: datetime.date


class Account_scheme(BaseModel):
    name: str
    description: Optional[str]
    balance: float
    created_at: datetime.date   

