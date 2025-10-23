import os, base64, secrets
from datetime import datetime

from fastapi import APIRouter, status, HTTPException
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

from app.schemas.auth import UserCreate, UserVerify, UserFetchUid, Token
from app.utils.auth import create_access_token, generate_uid
from app.services.database import db as db_service


router = APIRouter(prefix="/auth", tags=["auth"])


nonce_table = {} # redis?



@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    uid = generate_uid()
    new_user = await db_service.create_user(uid, user.pk)
    return {"uid": new_user.uid}
 

@router.get("/challenge", status_code=status.HTTP_200_OK)
async def challenge(uid: str):
    random_nonce = os.urandom(32)
    nonce_table[uid] = random_nonce
    return {"nonce": base64.b64encode(random_nonce).decode('utf-8')}


@router.post("/verify", status_code=status.HTTP_200_OK, response_model=Token)
async def verify_user(user: UserVerify):
    user_db = await db_service.get_user(user.uid)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with uid: {user.uid} not found")

    sig_bytes = base64.b64decode(user.sig)
    pk_bytes = base64.b64decode(user_db.pk)
    pk = Ed25519PublicKey.from_public_bytes(pk_bytes)

    try:
        pk.verify(sig_bytes, nonce_table[user.uid])
    except InvalidSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification failed"
        )
    
    del nonce_table[user.uid]
    return create_access_token(user.uid)


#replace with /me ?
@router.post("/fetch_uid", status_code=status.HTTP_200_OK)
async def fetch_uid(user: UserFetchUid):
    user_db = await db_service.get_user_by_pk(user.pk)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fetchi UID failed, user with provided pk was not found."
        )
    return {"uid": user_db.uid}
