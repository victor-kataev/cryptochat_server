from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.logging import logger


async def create_user(db: Session, uid: str, pk: str) -> User:
    user = User(uid=uid, pk=pk)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("new user created", uid=user.uid)
    return user
        

async def get_user(db: Session, uid: str) -> Optional[User]:
    return db.query(User).filter(User.uid == uid).first()
        
    
async def get_user_by_pk(db: Session, pk: str) -> Optional[User]:
    return db.query(User).filter(User.pk == pk).first()
