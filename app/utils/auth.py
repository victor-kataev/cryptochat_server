import secrets
from datetime import (
    datetime,
    timedelta
)
from typing import Optional

from jose import jwt

from app.core.config import settings
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

    