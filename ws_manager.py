from typing import Dict, List
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        # { usuario_id: [WebSocket, ...] }
        self.conexoes: Dict[int, List[WebSocket]] = {}

    async def conectar(self, usuario_id: int, websocket: WebSocket):
        await websocket.accept()
        self.conexoes.setdefault(usuario_id, []).append(websocket)

    def desconectar(self, usuario_id: int, websocket: WebSocket):
        lista = self.conexoes.get(usuario_id, [])
        if websocket in lista:
            lista.remove(websocket)
        if not lista:
            self.conexoes.pop(usuario_id, None)

    async def enviar_para_usuario(self, usuario_id: int, dados: dict):
        for ws in self.conexoes.get(usuario_id, []):
            try:
                await ws.send_json(dados)
            except Exception:
                pass  # conexão morta, ignora


ws_manager = WebSocketManager()









