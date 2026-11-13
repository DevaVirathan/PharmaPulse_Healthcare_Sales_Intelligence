"""Declarative base and shared column types."""

from sqlalchemy import BigInteger, Integer, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import JSON

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# BigInteger gives us BIGINT on PostgreSQL and still autoincrements in SQLite
# (used by the test suite).
BigIntPK = BigInteger().with_variant(Integer, "sqlite")

# JSONB on PostgreSQL, plain JSON on SQLite for portable tests.
JSONType = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
