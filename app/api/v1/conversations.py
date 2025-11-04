import json

from typing import Dict, List

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user, get_current_user_ws
from app.models.user import User
from app.core.logging import logger
from app.crud import user as user_crud
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
                await conn_manager.broadcast(f"{user.uid}: {body}", cid)
            # elif action == "read_receipt":
            #     ...
    except WebSocketDisconnect:
        logger.info(f"Websocket: user {user.uid} disconnected.")
        conn_manager.disconnect(websocket)
