"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db

# Importing models registers all tables on Base.metadata. Alias the package so
# it does not shadow the FastAPI application object below.
from app import models as _models  # noqa: F401
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def _sqlite_session() -> tuple[Session, object]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return testing_session(), engine


@pytest.fixture
def sqlite_session() -> Generator[Session, None, None]:
    """A lightweight SQLite session for endpoint tests that need SELECT 1."""

    session, engine = _sqlite_session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """An isolated SQLite database with the full schema created."""

    session, engine = _sqlite_session()
    Base.metadata.create_all(engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def db_client(client: TestClient, db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient whose get_db dependency uses the isolated SQLite session."""

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
