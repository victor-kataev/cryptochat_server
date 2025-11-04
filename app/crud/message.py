import uuid

from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.message import Message
from app.core.logging import logger


async def create_message(db: Session, body: str, user_uid, conv_id: int) -> Message:
    message = Message(
        id=uuid.uuid4(),
        body=body,
        sender_uid=user_uid,
        conversation_id=conv_id
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
