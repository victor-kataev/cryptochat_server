from sqlalchemy import QueuePool, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError


from app.core.config import settings
from app.core.logging import logger



Base = declarative_base()


# duplicate of settings.POSTGRES_URL
CONNECTION_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)


pool_size = settings.POSTGRES_POOL_SIZE
max_overflow = settings.POSTGRES_MAX_OVERFLOW


try:
    engine = create_engine(
        CONNECTION_URL,
        pool_pre_ping=True,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30, # connection timeout (seconds)
        pool_recycle=1800 # recycle timeout after 30 mins
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    logger.info(
        "database initialized",
        environment=settings.ENVIRONMENT.value,
        pool_size=pool_size,
        max_overflow=max_overflow
    )
except SQLAlchemyError as e:
    logger.error("database initialization error", error=str(e), environment=settings.ENVIRONMENT.value)
    # in production don't raise, let the app start even with db issues
    if settings.ENVIRONMENT.value != "production":
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

