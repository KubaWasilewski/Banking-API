from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import datetime
from uuid import UUID
from typing import Optional


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "person"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    surname: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128), unique=True)
    hashed_password_hex: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime.date]


class Account(Base):
    __tablename__ = "account"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("person.id"))
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True)
    balance: Mapped[float] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime.date]
