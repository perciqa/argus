"""WebSocket connection manager and router."""

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active: list[WebSocket] = []
        self.router = APIRouter()
        self.router.add_api_websocket_route("/ws/stream", self.stream_endpoint)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.remove(websocket)

    async def broadcast(self, event: str, data: Any) -> None:
        """Broadcast a named event with JSON payload to all connected clients."""
        message = json.dumps({"event": event, "data": data})
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

    async def stream_endpoint(self, websocket: WebSocket) -> None:
        await self.connect(websocket)
        try:
            while True:
                # Keep alive — clients can send pings
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.disconnect(websocket)


ws_manager = WebSocketManager()
