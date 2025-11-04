import os, base64, secrets
from datetime import datetime

from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.auth import UserCreate, UserVerify, UserFetchUid, Token
from app.utils.auth import create_access_token, generate_uid, verify_token
from app.utils.sanitization import sanitize_string
from app.services.database import get_db
from app.crud import user as user_crud
from app.core.logging import logger


router = APIRouter(prefix="/auth", tags=["auth"])


security = HTTPBearer()
nonce_table = {} # redis?


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
):
    logger.info("get_current_user")
    try:
        token = sanitize_string(credentials.credentials)
        uid = verify_token(token)
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user = await user_crud.get_user(db, uid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    except ValueError as ve:
        logger.error("token validation failed", error=str(ve))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_ws(
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket-compatible authentication dependency"""
    logger.info("get_current_user_ws")
    try:
        token = sanitize_string(token)
        uid = verify_token(token)
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        user = await user_crud.get_user(db, uid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except ValueError as ve:
        logger.error("token validation failed", error=str(ve))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid token format"
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    uid = generate_uid()
    try:
        new_user = await user_crud.create_user(db, uid, user.pk)
        return {"uid": new_user.uid}
    except SQLAlchemyError as e:
        logger.error(f"Failed to create a new user. {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with identical pk already exists."
        )
 

@router.get("/challenge", status_code=status.HTTP_200_OK)
async def challenge(uid: str):
    random_nonce = os.urandom(32)
    nonce_table[uid] = random_nonce
    return {"nonce": base64.b64encode(random_nonce).decode('utf-8')}


@router.post("/verify", status_code=status.HTTP_200_OK, response_model=Token)
async def verify_user(user: UserVerify, db: Session = Depends(get_db)):
    user_db = await user_crud.get_user(db, user.uid)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with uid: {user.uid} not found"
        )

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
async def fetch_uid(user: UserFetchUid, db: Session = Depends(get_db)):
    user_db = await user_crud.get_user_by_pk(db, user.pk)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fetching UID failed, user with provided pk was not found."
        )
    return {"uid": user_db.uid}
