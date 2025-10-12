import os, base64
from datetime import datetime

from fastapi import APIRouter, status, HTTPException
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


from app.schemas.auth import UserCreate, UserVerify


router = APIRouter(prefix="/auth", tags=["auth"])


db = {}
nonce_table = {}

def generate_uid():
    uid = "4566"
    return uid



@router.get("/")
async def read_auth():
    pass


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    uid = generate_uid()
    db[uid] = {"pk": user.pk, "created_at": datetime.now()}
    print(db)
    return {"uid": uid}
 

@router.get("/challenge", status_code=status.HTTP_200_OK)
async def challenge(uid: str):
    random_nonce = os.urandom(32)
    nonce_table[uid] = random_nonce
    return {"nonce": base64.b64encode(random_nonce).decode('utf-8')}


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_challenge(uid: str, user: UserVerify):
    sig_bytes = base64.b64decode(user.sig)
    user_pk_bytes = base64.b64decode(db[uid]['pk'])
    user_pk = Ed25519PublicKey.from_public_bytes(user_pk_bytes)

    try:
        user_pk.verify(sig_bytes, nonce_table[uid])
        return {"status": "Successfully verified"}
    except InvalidSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification failed"
        )
