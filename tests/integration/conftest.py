import os
import sys
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Inject a fake database module BEFORE any app code is imported.
# This prevents database.py from attempting a connection at module load time,
# while still giving models a real Base to register with.
#
# Uses a dedicated test Postgres database so tests run against the real
# dialect and constraint behaviour.  Override TEST_DATABASE_URL to point at
# any Postgres instance (e.g. a CI service container).
# ---------------------------------------------------------------------------
_TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://myuser:mypassword@localhost:5432/mydb",
)

_Base = declarative_base()
_engine = create_engine(_TEST_DB_URL)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _get_db():
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


_mock_db_module = MagicMock()
_mock_db_module.Base = _Base
_mock_db_module.engine = _engine
_mock_db_module.SessionLocal = _SessionLocal
_mock_db_module.get_db = _get_db

sys.modules["app.services.database"] = _mock_db_module

# ---------------------------------------------------------------------------
# Import models to register them with _Base, then create tables.
# ---------------------------------------------------------------------------
import app.models.user  # noqa: E402
import app.models.conversation  # noqa: E402
import app.models.message  # noqa: E402
import app.models.conversation_member  # noqa: E402

_Base.metadata.create_all(_engine)

# ---------------------------------------------------------------------------
# Import app and auth module after DB setup is complete.
# ---------------------------------------------------------------------------
from app.main import app  # noqa: E402
from app.api.v1 import auth as auth_module  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db():
    """Delete all rows from every table after each test."""
    yield
    with _engine.connect() as conn:
        for table in reversed(_Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture(autouse=True)
def clear_nonce_table():
    auth_module.nonce_table.clear()
    yield
    auth_module.nonce_table.clear()


@pytest.fixture
def db():
    session = _SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)
