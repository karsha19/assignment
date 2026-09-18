from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.core.security import decode_token
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket, token: str = Query(...)):
    try:
        decode_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
