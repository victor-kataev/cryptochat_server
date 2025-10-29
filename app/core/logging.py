import structlog

from app.core.config import settings


logger = structlog.get_logger()
logger.info(
    "logger initialized",
    environment=settings.ENVIRONMENT.value,
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT
)