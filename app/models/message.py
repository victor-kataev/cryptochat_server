from datetime import datetime, UTC

from sqlalchemy import Column, UUID, Text, DateTime, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from app.services.database import Base


class Message(Base):
    __tablename__ = 'messages'

    id = Column(UUID, primary_key=True, index=True)
    body = Column(Text, nullable=False)
    sender_uid = Column(String(30), ForeignKey("users.uid"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    created_at = Column(DateTime, default=datetime.now(UTC))
    
    sender = relationship('User', back_populates='messages')
    conversation = relationship('Conversation', back_populates='messages')
