from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session

from models import Notificacao, Usuario
from schemas import NotificacaoCreate, NotificacaoResponse
from dependencies import pegar_sessao, verificar_token, verificar_token_ws
from ws_manager import ws_manager
from email_service import enviar_email_notificacao

notificacao_router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


# ─────────────────────────────────────────────
# WEBSOCKET — /notificacoes/ws
# ─────────────────────────────────────────────
@notificacao_router.websocket("/ws")
async def websocket_notificacoes(
    websocket: WebSocket,
    usuario: Usuario = Depends(verificar_token_ws),
    session: Session = Depends(pegar_sessao),
):
    await ws_manager.conectar(usuario.id, websocket)
    try:
        # Envia notificações não lidas assim que conecta
        nao_lidas = (
            session.query(Notificacao)
            .filter(Notificacao.usuario_id == usuario.id, Notificacao.lida == False)
            .order_by(Notificacao.criado_em.desc())
            .all()
        )
        for n in nao_lidas:
            await websocket.send_json(_serializar(n))

        # Mantém a conexão viva aguardando pings do cliente
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.desconectar(usuario.id, websocket)


# ─────────────────────────────────────────────
# CRIAR NOTIFICAÇÃO
# ─────────────────────────────────────────────
@notificacao_router.post("/", response_model=NotificacaoResponse, status_code=201)
async def criar_notificacao(
    dados: NotificacaoCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    destinatario = session.query(Usuario).filter(Usuario.id == dados.usuario_id).first()
    if not destinatario:
        raise HTTPException(status_code=404, detail="Usuário destinatário não encontrado")

    notificacao = Notificacao(
        usuario_id=dados.usuario_id,
        titulo=dados.titulo,
        mensagem=dados.mensagem,
        tipo=dados.tipo,
        lida=False,
    )
    session.add(notificacao)
    session.commit()
    session.refresh(notificacao)

    # 1️⃣ Tempo real via WebSocket
    await ws_manager.enviar_para_usuario(dados.usuario_id, _serializar(notificacao))

    # 2️⃣ Email em background
    if destinatario.email and dados.enviar_email:
        background_tasks.add_task(
            enviar_email_notificacao,
            destinatario.email,
            dados.titulo,
            dados.mensagem,
        )

    return notificacao


# ─────────────────────────────────────────────
# LISTAR NOTIFICAÇÕES
# ─────────────────────────────────────────────
@notificacao_router.get("/", response_model=list[NotificacaoResponse])
async def listar_notificacoes(
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    return (
        session.query(Notificacao)
        .filter(Notificacao.usuario_id == usuario.id)
        .order_by(Notificacao.criado_em.desc())
        .all()
    )


# ─────────────────────────────────────────────
# MARCAR COMO LIDA
# ─────────────────────────────────────────────
@notificacao_router.put("/{notificacao_id}/lida", response_model=NotificacaoResponse)
async def marcar_como_lida(
    notificacao_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    notificacao = _buscar_ou_404(session, notificacao_id, usuario.id)
    notificacao.lida = True
    session.commit()
    session.refresh(notificacao)
    return notificacao


# ─────────────────────────────────────────────
# MARCAR TODAS COMO LIDAS
# ─────────────────────────────────────────────
@notificacao_router.put("/lidas", status_code=200)
async def marcar_todas_como_lidas(
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    session.query(Notificacao).filter(
        Notificacao.usuario_id == usuario.id,
        Notificacao.lida == False,
    ).update({"lida": True})
    session.commit()
    return {"msg": "Todas as notificações foram marcadas como lidas"}


# ─────────────────────────────────────────────
# DELETAR NOTIFICAÇÃO
# ─────────────────────────────────────────────
@notificacao_router.delete("/{notificacao_id}")
async def deletar_notificacao(
    notificacao_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    notificacao = _buscar_ou_404(session, notificacao_id, usuario.id)
    session.delete(notificacao)
    session.commit()
    return {"msg": "Notificação deletada com sucesso"}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _buscar_ou_404(session: Session, notificacao_id: int, usuario_id: int) -> Notificacao:
    n = session.query(Notificacao).filter(
        Notificacao.id == notificacao_id,
        Notificacao.usuario_id == usuario_id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return n


def _serializar(n: Notificacao) -> dict:
    return {
        "id": n.id,
        "titulo": n.titulo,
        "mensagem": n.mensagem,
        "tipo": n.tipo,
        "lida": n.lida,
        "criado_em": n.criado_em.isoformat(),
        "seletivo_id": n.seletivo_id if hasattr(n, "seletivo_id") else None,
    }