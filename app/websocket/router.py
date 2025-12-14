from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import WebSocketManager
from app.auth.service import decode_jwt_token

websocket_router = APIRouter()


@websocket_router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    manager = WebSocketManager.get_instance()
    user_id = None

    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Token required")
            return

        try:
            payload = decode_jwt_token(token)
            if not payload:
                await websocket.close(code=1008, reason="Invalid token")
                return
            user_id = int(payload.user_id)
        except Exception:
            await websocket.close(code=1008, reason="Invalid token")
            return

        await manager.connect(websocket, user_id)

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
    except Exception as e:
        if user_id:
            manager.disconnect(websocket, user_id)
        await websocket.close(code=1011, reason=str(e))
