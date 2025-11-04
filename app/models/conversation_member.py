from datetime import datetime, UTC

from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from app.services.database import Base


class ConversationMember(Base):
    __tablename__ = "conversation_members"

    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.now(UTC))

    user = relationship("User", back_populates="conversation_members")
    conversation = relationship("Conversation", back_populates="members")

    __table_args__ = (
        PrimaryKeyConstraint("conversation_id", "user_id"),
    )
    