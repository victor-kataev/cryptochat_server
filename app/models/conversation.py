from datetime import datetime, UTC

from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.orm import relationship

from app.services.database import Base


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))

    messages = relationship('Message', back_populates='conversation')
    members = relationship('ConversationMember', back_populates='conversation')
