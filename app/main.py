from datetime import datetime

from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.api.v1.api import api_router
from app.core.logging import logger
from app.utils.auth import verify_token


app = FastAPI()

app.include_router(api_router)


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <h2>Your ID: <span id=ws-id></span></h2>
        <input id="messageText" type="text" placeholder="Type a message...">
        <button onclick="sendMessage()">Send</button>
        <ul id='messages'></ul>

        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8080/ws/${client_id}`);
            
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                message.textContent = event.data;
                messages.appendChild(message);
            };
            
            function sendMessage() {
                var input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def read_root():
    return HTMLResponse(html)


from typing import List

class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, msg: str):
        for conn in self.connections:
            await conn.send_text(msg)


conn_manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    uid = verify_token(token)
    await conn_manager.connect(websocket)
    logger.info(f"{uid} connected")
    try:
        while True:
            text = await websocket.receive_text()
            logger.info(f"{uid} says: {text}")
            await conn_manager.broadcast(f"{uid}: {text}")
    except WebSocketDisconnect:
        conn_manager.disconnect(websocket)
        await conn_manager.broadcast(f"{uid} left")
