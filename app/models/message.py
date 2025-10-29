from datetime import datetime, UTC

from sqlalchemy import Column, UUID, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.services.database import Base


class Message(Base):
    __tablename__ = 'messages'

    id = Column(UUID, primary_key=True, index=True)
    body = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    created_at = Column(DateTime, default=datetime.now(UTC))
    
    sender = relationship('User', back_populates='users')
    conversation = relationship('Conversation', back_populates='conversations')
