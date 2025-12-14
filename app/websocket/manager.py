from typing import Dict, Set
from fastapi import WebSocket


class WebSocketManager:
    _instance = None
    _connections: Dict[int, Set[WebSocket]] = {}

    def __init__(self):
        if WebSocketManager._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        self._connections = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self._connections:
            disconnected = set()
            for connection in self._connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            for connection in disconnected:
                self._connections[user_id].discard(connection)

    async def broadcast(self, message: dict):
        disconnected = []
        for user_id, connections in self._connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append((user_id, connection))
        for user_id, connection in disconnected:
            if user_id in self._connections:
                self._connections[user_id].discard(connection)
