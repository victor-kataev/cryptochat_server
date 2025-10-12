import re

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
    

class UserLogin(BaseModel):
    pk: str


class UserVerify(BaseModel):
    sig: str