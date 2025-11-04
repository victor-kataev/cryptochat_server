import uuid

from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.message import Message
from app.core.logging import logger


async def get_messages_of_conversation(db: Session, conv_id: int, limit: int = 10, offset: int = 0) -> List[Message]:
    logger.info(f"Fetching messages of chat_id: {conv_id}")
    messages = db.query(Message).filter(Message.conversation_id == conv_id).limit(limit).all()
    return messages
