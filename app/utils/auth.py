from datetime import (
    datetime,
    timedelta
)
from typing import Optional

from jose import jwt

from app.core.config import settings
from app.schemas.auth import Token



def create_access_token(thread_id: str, expires_delta: Optional[timedelta] = None) -> Token:
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.JWT_TOKEN_EXPIRE_MINUTES)

    to_encrypt = {
        "sub": thread_id,
        "exp": expire,
        "iat": datetime.now().isoformat()
    }

    encoded_jwt = jwt.encode(to_encrypt, settings.JWT_SECRETE_KEY, algorithm=settings.JWT_ALGORITHM)
    return Token(access_token=encoded_jwt, expires_at=expire)

    