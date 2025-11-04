from datetime import datetime

from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse

from app.api.v1.api import api_router
from app.core.logging import logger
from app.utils.auth import verify_token
from app.api.v1.auth import get_current_user, get_current_user_ws
from app.models.user import User


app = FastAPI()

app.include_router(api_router)



@app.get("/")
async def read_root():
    return {"data": "root"}

