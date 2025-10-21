import re
from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    SecretStr,
    field_validator
)

"""
TODO:
- verify pk
- verify uid ?
"""


class UserCreate(BaseModel):
    pk: str
    

class UserFetchUid(BaseModel):
    pk: str

class UserVerify(BaseModel):
    uid: str
    sig: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
