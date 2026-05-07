from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from models import Seletivo, Favorito, Usuario, EtapaSeletivo, Edital, DocumentoEdital
from schemas import (
    SeletivoCreateSchema, SeletivoUpdateSchema, SeletivoResponse,
    EtapaResponse, EditalResponse, DocumentoEditalCreate, EditalCreate )
from dependencies import pegar_sessao, verificar_token, apenas_coordenador

seletivo_router = APIRouter(prefix="/seletivos", tags=["Seletivos"])
coordenador_router = APIRouter(prefix="/coordenador/seletivos", tags=["Coordenador — Seletivos"])


# HELPER: monta dict com campo "favoritado"

def montar_response(seletivo: Seletivo, usuario_id: int, session: Session) -> dict:
    favoritado = session.query(Favorito).filter(
        Favorito.usuario_id == usuario_id,
        Favorito.seletivo_id == seletivo.id,
    ).first() is not None

    return {
        "id": seletivo.id,
        "titulo": seletivo.titulo,
        "descricao": seletivo.descricao,
        "area": seletivo.area,
        "subarea": seletivo.subarea,
        "data_inicio": seletivo.data_inicio,
        "data_fim": seletivo.data_fim,
        "data_prova": seletivo.data_prova,
        "link_inscricao": seletivo.link_inscricao,
        "bolsa_valor": seletivo.bolsa_valor,
        "nivel": seletivo.nivel,
        "favoritos": seletivo.favoritos,
        "nota_capes": seletivo.nota_capes,
        "coordenador_id": seletivo.coordenador_id,
        "coordenador_nome": seletivo.coordenador.nome if seletivo.coordenador else None,
        "favoritado": favoritado,
        "criado_em": seletivo.criado_em,
        "etapas": [{"id": e.id, "ordem": e.ordem, "descricao": e.descricao} for e in seletivo.etapas],
        "editais": [
            {
                "id": ed.id,
                "seletivo_id": ed.seletivo_id,
                "titulo": ed.titulo,
                "descricao": ed.descricao,
                "vagas": ed.vagas,
                "data_inicio_inscricao": ed.data_inicio_inscricao,
                "data_fim_inscricao": ed.data_fim_inscricao,
                "data_prova": ed.data_prova,
                "criado_em": ed.criado_em,
                "documentos": [
                    {
                        "id": d.id,
                        "titulo": d.titulo,
                        "url_arquivo": d.url_arquivo,
                        "url_externo": d.url_externo,
                        "is_pdf": d.is_pdf,
                    }
                    for d in ed.documentos
                ],
            }
            for ed in seletivo.editais
        ],
    }


# ROTAS DO ESTUDANTE

# LISTAR TODOS OS SELETIVOS

@seletivo_router.get("/")
async def listar_seletivos(
    area: Optional[str]  = Query(None),
    nivel: Optional[str] = Query(None),
    busca: Optional[str] = Query(None),
    session: Session     = Depends(pegar_sessao),
    usuario: Usuario     = Depends(verificar_token),
):
    query = session.query(Seletivo)

    if area:
        query = query.filter(Seletivo.area.ilike(f"%{area}%"))
    if nivel:
        query = query.filter(Seletivo.nivel.ilike(f"%{nivel}%"))
    if busca:
        query = query.filter(
            Seletivo.titulo.ilike(f"%{busca}%") | Seletivo.descricao.ilike(f"%{busca}%")
        )

    seletivos = query.order_by(Seletivo.data_fim.asc()).all()
    return [montar_response(s, usuario.id, session) for s in seletivos]


# DETALHE DE UM SELETIVO

@seletivo_router.get("/{seletivo_id}")
async def detalhe_seletivo(
    seletivo_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    seletivo = session.query(Seletivo).filter(Seletivo.id == seletivo_id).first()

    if not seletivo:
        raise HTTPException(status_code=404, detail="Seletivo não encontrado")

    return montar_response(seletivo, usuario.id, session)


# LISTAR FAVORITOS

@seletivo_router.get("/favoritos/lista")
async def listar_favoritos(
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    favoritos = (
        session.query(Seletivo)
        .join(Favorito, Favorito.seletivo_id == Seletivo.id)
        .filter(Favorito.usuario_id == usuario.id)
        .all()
    )
    return [montar_response(s, usuario.id, session) for s in favoritos]


# FAVORITAR

@seletivo_router.post("/{seletivo_id}/favoritar")
async def favoritar(
    seletivo_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    seletivo = session.query(Seletivo).filter(Seletivo.id == seletivo_id).first()
    if not seletivo:
        raise HTTPException(status_code=404, detail="Seletivo não encontrado")

    ja_favoritado = session.query(Favorito).filter(
        Favorito.usuario_id == usuario.id,
        Favorito.seletivo_id == seletivo_id,
    ).first()

    if ja_favoritado:
        raise HTTPException(status_code=400, detail="Seletivo já está nos favoritos")

    favorito = Favorito(usuario_id=usuario.id, seletivo_id=seletivo_id)
    session.add(favorito)
    session.commit()

    return {"msg": "Seletivo adicionado aos favoritos"}


# DESFAVORITAR

@seletivo_router.delete("/{seletivo_id}/favoritar")
async def desfavoritar(
    seletivo_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    favorito = session.query(Favorito).filter(
        Favorito.usuario_id == usuario.id,
        Favorito.seletivo_id == seletivo_id,
    ).first()

    if not favorito:
        raise HTTPException(status_code=404, detail="Seletivo não está nos favoritos")

    session.delete(favorito)
    session.commit()

    return {"msg": "Seletivo removido dos favoritos"}


# ROTAS DO COORDENADOR  


# CRIAR SELETIVO

@coordenador_router.post("/")
async def criar_seletivo(
    dados: SeletivoCreateSchema,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    novo = Seletivo(
        titulo=dados.titulo,
        descricao=dados.descricao,
        area=dados.area,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
        link_inscricao=dados.link_inscricao,
        bolsa_valor=dados.bolsa_valor,
        nivel=dados.nivel,
        coordenador_id=usuario.id,
    )

    session.add(novo)
    session.commit()
    session.refresh(novo)

    return montar_response(novo, usuario.id, session)


# MEUS SELETIVOS

@coordenador_router.get("/")
async def meus_seletivos(
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    seletivos = (
        session.query(Seletivo)
        .filter(Seletivo.coordenador_id == usuario.id)
        .order_by(Seletivo.criado_em.desc())
        .all()
    )
    return [montar_response(s, usuario.id, session) for s in seletivos]


# DETALHE DO MEU SELETIVO

@coordenador_router.get("/{seletivo_id}")
async def detalhe_meu_seletivo(
    seletivo_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    seletivo = session.query(Seletivo).filter(
        Seletivo.id == seletivo_id,
        Seletivo.coordenador_id == usuario.id,
    ).first()

    if not seletivo:
        raise HTTPException(status_code=404, detail="Seletivo não encontrado")

    return montar_response(seletivo, usuario.id, session)


# EDITAR SELETIVO

@coordenador_router.put("/{seletivo_id}")
async def editar_seletivo(
    seletivo_id: int,
    dados: SeletivoUpdateSchema,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    seletivo = session.query(Seletivo).filter(
        Seletivo.id == seletivo_id,
        Seletivo.coordenador_id == usuario.id,
    ).first()

    if not seletivo:
        raise HTTPException(status_code=404, detail="Seletivo não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(seletivo, campo, valor)

    session.commit()
    session.refresh(seletivo)

    return montar_response(seletivo, usuario.id, session)


# DELETAR SELETIVO

@coordenador_router.delete("/{seletivo_id}")
async def deletar_seletivo(
    seletivo_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    seletivo = session.query(Seletivo).filter(
        Seletivo.id == seletivo_id,
        Seletivo.coordenador_id == usuario.id,
    ).first()

    if not seletivo:
        raise HTTPException(status_code=404, detail="Seletivo não encontrado")

    session.delete(seletivo)
    session.commit()

    return {"msg": "Seletivo deletado com sucesso"}



# ETAPAS


@coordenador_router.post("/{seletivo_id}/etapas")
async def adicionar_etapa(
    seletivo_id: int,
    dados: EtapaResponse,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    seletivo = session.query(Seletivo).filter(
        Seletivo.id == seletivo_id,
        Seletivo.coordenador_id == usuario.id,
    ).first()

    if not seletivo:
        raise HTTPException(status_code=404, detail="Seletivo não encontrado")

    etapa = EtapaSeletivo(
        seletivo_id=seletivo_id,
        ordem=dados.ordem,
        descricao=dados.descricao,
    )
    session.add(etapa)
    session.commit()
    session.refresh(etapa)

    return {"id": etapa.id, "ordem": etapa.ordem, "descricao": etapa.descricao}


@coordenador_router.delete("/{seletivo_id}/etapas/{etapa_id}")
async def deletar_etapa(
    seletivo_id: int,
    etapa_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    etapa = session.query(EtapaSeletivo).filter(
        EtapaSeletivo.id == etapa_id,
        EtapaSeletivo.seletivo_id == seletivo_id,
    ).first()

    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa não encontrada")

    session.delete(etapa)
    session.commit()

    return {"msg": "Etapa deletada com sucesso"}



# EDITAIS


@coordenador_router.post("/{seletivo_id}/editais")
async def adicionar_edital(
    seletivo_id: int,
    dados: EditalCreate,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    seletivo = session.query(Seletivo).filter(
        Seletivo.id == seletivo_id,
        Seletivo.coordenador_id == usuario.id,
    ).first()

    if not seletivo:
        raise HTTPException(status_code=404, detail="Seletivo não encontrado")

    edital = Edital(
        seletivo_id=seletivo_id,
        titulo=dados.titulo,
        descricao=dados.descricao,
        vagas=dados.vagas,
        data_inicio_inscricao=dados.data_inicio_inscricao,
        data_fim_inscricao=dados.data_fim_inscricao,
        data_prova=dados.data_prova,
    )
    session.add(edital)
    session.flush()  # pega o id antes do commit

    for doc in dados.documentos:
        documento = DocumentoEdital(
            edital_id=edital.id,
            titulo=doc.titulo,
            url_arquivo=doc.url_arquivo,
            url_externo=doc.url_externo,
            is_pdf=doc.is_pdf,
        )
        session.add(documento)

    session.commit()
    session.refresh(edital)

    return {
        "id": edital.id,
        "seletivo_id": edital.seletivo_id,
        "titulo": edital.titulo,
        "descricao": edital.descricao,
        "vagas": edital.vagas,
        "data_inicio_inscricao": edital.data_inicio_inscricao,
        "data_fim_inscricao": edital.data_fim_inscricao,
        "data_prova": edital.data_prova,
        "criado_em": edital.criado_em,
        "documentos": [
            {
                "id": d.id,
                "titulo": d.titulo,
                "url_arquivo": d.url_arquivo,
                "url_externo": d.url_externo,
                "is_pdf": d.is_pdf,
            }
            for d in edital.documentos
        ],
    }


@coordenador_router.delete("/{seletivo_id}/editais/{edital_id}")
async def deletar_edital(
    seletivo_id: int,
    edital_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(apenas_coordenador),
):
    edital = session.query(Edital).filter(
        Edital.id == edital_id,
        Edital.seletivo_id == seletivo_id,
    ).first()

    if not edital:
        raise HTTPException(status_code=404, detail="Edital não encontrado")

    session.delete(edital)
    session.commit()

    return {"msg": "Edital deletado com sucesso"}