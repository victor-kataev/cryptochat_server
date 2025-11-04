import re
from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    SecretStr,
    field_validator,
    Field
)

class MessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    sender_uid: str
    conversation_id: int
    body: str
    created_at: datetime

class MessagesListResponse(BaseModel):
    count: int
    messages: list[MessageResponse]
