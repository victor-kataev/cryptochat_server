import json

from typing import Dict, List

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.auth import get_current_user, get_current_user_ws
from app.models.user import User
from app.core.logging import logger
from app.schemas.conversation import MessagesListResponse, MessageResponse
from app.crud import (
    conversation as conv_crud,
    message as msg_crud,
    user as user_crud
)
from app.services.database import get_db



router = APIRouter(prefix="/conversations", tags=["conversations"])



class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()

    def disconnect(self, ws: WebSocket):
        for cid, conns in self.active_connections.items():
            if ws in conns:
                conns.remove(ws)

    def subscribe(self, ws: WebSocket, conv_id: int):
        self.active_connections.setdefault(conv_id, []).append(ws)

    async def broadcast(self, msg: str, conv_id: int):
        for conn in self.active_connections[conv_id]:
            await conn.send_text(msg)
    


conn_manager = ConnectionManager()


@router.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    user: User = Depends(get_current_user_ws),
    db: Session = Depends(get_db)
):
    await conn_manager.connect(websocket)

    for cm in user.conversation_members:
        conn_manager.subscribe(websocket, cm.conversation_id)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            action = data["action"]
            cid = data["conversation_id"]

            if action == "send_message":
                body = data["body"]
                message = await msg_crud.create_message(db, body, user.uid, cid)
                if not message:
                    raise SQLAlchemyError()
                await conn_manager.broadcast(f"{user.uid}: {body}", cid)
            # elif action == "read_receipt":
            #     ...
    except WebSocketDisconnect:
        logger.info(f"Websocket: user {user.uid} disconnected.")
        conn_manager.disconnect(websocket)
    except SQLAlchemyError as er:
        logger.erro(f"Failed to create a new message. {er}")
        raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Failed to create a new message"
            )


@router.get("/{id}/messages", response_model=MessagesListResponse)
async def get_conversation_messages(
        id: int, limit: int = 100, offset: int = 0, 
        db: Session = Depends(get_db), 
        user: User = Depends(get_current_user)
    ):
    messages_rows = await conv_crud.get_messages_of_conversation(db, id, limit, offset)
    return MessagesListResponse(
        count=len(messages_rows),
        messages=[MessageResponse.model_validate(msg) for msg in messages_rows]
    )
