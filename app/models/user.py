from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.services.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, default=None)
    uid = Column(String(30), unique=True, index=True)
    pk = Column(String(200), unique=True)
    created_at = Column(DateTime, default=datetime.now(UTC))

    messages = relationship('Message', back_populates='sender')
