from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Notificacao, Usuario
from schemas import NotificacaoResponse
from dependencies import pegar_sessao, verificar_token

notificacao_router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


# LISTAR NOTIFICAÇÕES

@notificacao_router.get("/")
async def listar_notificacoes(
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    notificacoes = (
        session.query(Notificacao)
        .filter(Notificacao.usuario_id == usuario.id)
        .order_by(Notificacao.criado_em.desc())
        .all()
    )
    return notificacoes


# MARCAR COMO LIDA

@notificacao_router.put("/{notificacao_id}/lida")
async def marcar_como_lida(
    notificacao_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    notificacao = session.query(Notificacao).filter(
        Notificacao.id == notificacao_id,
        Notificacao.usuario_id == usuario.id,
    ).first()

    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    notificacao.lida = True
    session.commit()
    session.refresh(notificacao)

    return notificacao


# DELETAR NOTIFICAÇÃO

@notificacao_router.delete("/{notificacao_id}")
async def deletar_notificacao(
    notificacao_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    notificacao = session.query(Notificacao).filter(
        Notificacao.id == notificacao_id,
        Notificacao.usuario_id == usuario.id,
    ).first()

    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    session.delete(notificacao)
    session.commit()

    return {"msg": "Notificação deletada com sucesso"}
