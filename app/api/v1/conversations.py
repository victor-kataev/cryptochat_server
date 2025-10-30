import json

from typing import Dict, List

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect

from app.api.v1.auth import get_current_user
from app.models.user import User
from app.core.logging import logger


router = APIRouter(prefix="/conversations", tags=["conversations"])



class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()

    def disconnect(self, ws: WebSocket):
        for _, conns in self.active_connections.items():
            if ws in conns:
                conns.remove(ws)

    def subscribe(self, ws: WebSocket, conv_id: int):
        self.active_connections.setdefault(conv_id, []).append(ws)
        

conn_manager = ConnectionManager()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, user: User = Depends(get_current_user)):
    await conn_manager.connect(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            action = data["action"]

            if action == "subscribe":
                ...
            elif action == "send_message":
                ...
            elif action == "read_receipt":
                ...
    except WebSocketDisconnect:
        logger.info(f"Websocket: user {user.uid} disconnected.")
