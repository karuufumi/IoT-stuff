# controller/RealtimeController.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from realtime.connection_manager import manager

router = APIRouter()

@router.websocket("/ws/metrics")
async def metrics_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive (client doesn’t need to send)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)