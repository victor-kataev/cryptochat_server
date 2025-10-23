from typing import Optional

from sqlalchemy import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from sqlmodel import (
    Session, 
    create_engine, 
    SQLModel,
    select
)

from app.core.config import settings
from app.core.logging import logger

from app.models.user import User


class DatabaseSevice:
    """
    Service class for database operations.
    This class uses SQLModel for ORM and connection pool
    """
    def __init__(self):
        pool_size = settings.POSTGRES_POOL_SIZE
        max_overflow = settings.POSTGRES_MAX_OVERFLOW

        connection_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

        try:
            self.engine = create_engine(
                connection_url,
                pool_pre_ping=True,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=30, # connection timeout (seconds)
                pool_recycle=1800 # recycle timeout after 30 mins
            )

            # create tables only if they don't exist
            SQLModel.metadata.create_all(self.engine)

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


    async def create_user(self, uid: str, pk: str) -> User:
        with Session(self.engine) as session:
            user = User(uid=uid, pk=pk)
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info("new user created", uid=user.uid)
            return user
        

    async def get_user(self, uid: str) -> Optional[User]:
        with Session(self.engine) as session:
            statement = select(User).where(User.uid == uid)
            user = session.exec(statement).first()
            return user
        
    
    async def get_user_by_pk(self, pk: str) -> Optional[User]:
        with Session(self.engine) as session:
            stmt = select(User).where(User.pk == pk)
            user = session.exec(stmt).first()
            return user



db = DatabaseSevice()
