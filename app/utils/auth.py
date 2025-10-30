import secrets
import re


from datetime import (
    datetime,
    timedelta
)
from typing import Optional

from jose import jwt, JWTError

from app.core.config import settings
from app.core.logging import logger
from app.schemas.auth import Token



CROCKFORD_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def base32crockford(num: int, length: int = 8) -> str:
    chars = []
    for _ in range(length):
        chars.append(CROCKFORD_ALPHABET[num % 32])
        num //= 32
    return "".join(reversed(chars))


def generate_uid() -> str:
    num = int.from_bytes(secrets.token_bytes(5), "big")
    return base32crockford(num)


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

    encoded_jwt = jwt.encode(to_encrypt, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return Token(access_token=encoded_jwt, expires_at=expire)


def verify_token(token: str) -> Optional[str]:
    if not token or not isinstance(token, str):
        logger.error("empty token")
        raise ValueError("Token must be a non-empty string")
    
    if not re.match(r"^[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.[A-Za-z0-9_]+$", token):
        logger.error("invalid token format")
        raise ValueError("Token format is invalid - expected JWT format")
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        thread_id = payload["sub"]
        if not thread_id:
            logger.error("thread id is empty")
            return None
        logger.info("token verified", thread_id=thread_id)
        return thread_id
    except JWTError as er:
        logger.error("token verification failed", error=str(er))
        return None
