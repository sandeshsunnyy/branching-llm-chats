from sqlalchemy.sql import func 
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class TimestampMixin:
    created_at : Mapped[datetime] = mapped_column(server_default=func.now())

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)