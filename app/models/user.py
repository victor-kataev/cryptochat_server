from datetime import datetime, UTC

from sqlmodel import SQLModel, Field



class User(SQLModel, table=True):
    id: int = Field(primary_key=True, default=None)
    uid: str = Field(unique=True, index=True)
    pk: str = Field(unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
