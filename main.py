from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import websockets
app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_counter = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.client_counter += 1
        self.active_connections.append(websocket)
        return self.client_counter

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

class Message(BaseModel):
    content: str

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    assigned_client_id = await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{assigned_client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{assigned_client_id} has left the chat")

@app.post("/broadcast")
async def broadcast_message(message: Message):
    await manager.broadcast(message.content)
    return {"message": "Message broadcasted"}
