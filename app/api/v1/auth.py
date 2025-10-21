import os, base64, secrets
from datetime import datetime

from fastapi import APIRouter, status, HTTPException
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


from app.schemas.auth import UserCreate, UserVerify, UserFetchUid, Token
from app.utils.auth import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


db = {}
pk_to_uid = {}
nonce_table = {}


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


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    uid = generate_uid()
    db[uid] = {"pk": user.pk, "created_at": datetime.now()}
    pk_to_uid[user.pk] = uid
    return {"uid": uid}
 

@router.get("/challenge", status_code=status.HTTP_200_OK)
async def challenge(uid: str):
    random_nonce = os.urandom(32)
    nonce_table[uid] = random_nonce
    return {"nonce": base64.b64encode(random_nonce).decode('utf-8')}


@router.post("/verify", status_code=status.HTTP_200_OK, response_model=Token)
async def verify_user(user: UserVerify):
    sig_bytes = base64.b64decode(user.sig)
    user_pk_bytes = base64.b64decode(db[user.uid]['pk'])
    user_pk = Ed25519PublicKey.from_public_bytes(user_pk_bytes)

    try:
        user_pk.verify(sig_bytes, nonce_table[user.uid])
    except InvalidSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification failed"
        )
    
    del nonce_table[user.uid]
    return create_access_token(user.uid)


@router.post("/fetch_uid", status_code=status.HTTP_200_OK)
async def fetch_uid(user: UserFetchUid):
    print(user.pk)
    print(pk_to_uid)
    if not user.pk in pk_to_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fetchi UID failed, provided pk was not found."
        )
    return {"uid": pk_to_uid[user.pk]}
