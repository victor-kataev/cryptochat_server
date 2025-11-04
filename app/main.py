from datetime import datetime

from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse

from app.api.v1.api import api_router
from app.core.logging import logger


app = FastAPI()

app.include_router(api_router)



@app.get("/")
async def read_root():
    return {"data": "root"}

