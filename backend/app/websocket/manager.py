import json
import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("okdriver.websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected (total=%d)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected (total=%d)", len(self.active_connections))

    async def broadcast(self, event_type: str, payload: dict):
        message = json.dumps({"type": event_type, "data": payload}, default=str)
        logger.info("Broadcasting %s to %d connections", event_type, len(self.active_connections))
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                logger.exception("Error sending WS message; marking connection stale")
                stale.append(connection)
        for conn in stale:
            self.disconnect(conn)


manager = ConnectionManager()
