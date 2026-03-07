import sys
from unittest.mock import MagicMock
from sqlalchemy.orm import declarative_base

# Inject a fake database module before any app code is imported.
# database.py calls Base.metadata.create_all(engine) at module level,
# which would attempt a real Postgres connection during collection.
_Base = declarative_base()

_mock_db_module = MagicMock()
_mock_db_module.Base = _Base
_mock_db_module.engine = MagicMock()
_mock_db_module.SessionLocal = MagicMock()
_mock_db_module.get_db = MagicMock()

sys.modules["app.services.database"] = _mock_db_module
