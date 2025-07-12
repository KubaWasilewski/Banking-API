from pydantic import BaseModel, model_validator, EmailStr
from typing import Optional
from uuid import UUID
import datetime


class Token_scheme(BaseModel):
    access_token: str
    token_type: str


class Person_scheme(BaseModel):
    name: str
    surname: str
    email: str
    created_at: datetime.date

    class Config:
        from_attributes = True


class Account_scheme(BaseModel):
    name: str
    description: Optional[str]
    balance: float
    created_at: datetime.date

    class Config:
        from_attributes = True


class Person_register(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str

    @model_validator(mode="after")
    def person_register_validator(self):
        if not self.name.strip() or not self.surname.strip() or not self.password.strip():
            raise ValueError("name, surname or password can't be blank")
        return self


class Person_login(BaseModel):
    email: EmailStr
    password: str

    @model_validator(mode="after")
    def person_login_validator(self):
        if not self.password.strip():
            raise ValueError("password can't be blank")
        return self


class Account_register(BaseModel):
    name: str
    description: Optional[str]

    @model_validator(mode="after")
    def account_register_validator(self):
        if not self.name.strip():
            raise ValueError("name can't be blank")
        return self
