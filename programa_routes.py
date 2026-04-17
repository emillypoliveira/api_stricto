from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional, List

from models import Programa, Curso, LinhaPesquisa, FavoritoPrograma, Usuario
from schemas import ProgramaResponse
from dependencies import pegar_sessao, verificar_token

programa_router = APIRouter(prefix="/programas", tags=["Programas"])


#HELPER OTIMIZADO

def montar_response(programa: Programa, favoritos_ids: set) -> dict:
    niveis = [c.nivel_label or c.nivel for c in programa.cursos if c.situacao == "ATIVO"]
    linhas = [lp.descricao for lp in programa.linhas_pesquisa]

    return {
        "id": programa.id,
        "nome": programa.nome,
        "sigla": programa.sigla,
        "situacao": programa.situacao,
        "nome_ies": programa.nome_ies,
        "sigla_ies": programa.sigla_ies,
        "categoria_ies": programa.categoria_ies,
        "uf": programa.uf,
        "municipio": programa.municipio,
        "regiao": programa.regiao,
        "grande_area": programa.grande_area,
        "area_conhecimento": programa.area_conhecimento,
        "area_avaliacao": programa.area_avaliacao,
        "nota": programa.nota,
        "ano_inicio": programa.ano_inicio,
        "niveis": niveis,
        "linhas_pesquisa": linhas,
        "favoritado": programa.id in favoritos_ids,
    }


#LISTAR FAVORITOS (ANTES DO /{id})

@programa_router.get("/favoritos/lista")
async def listar_favoritos(
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    programas = (
        session.query(Programa)
        .join(FavoritoPrograma, FavoritoPrograma.programa_id == Programa.id)
        .options(joinedload(Programa.cursos), joinedload(Programa.linhas_pesquisa))
        .filter(FavoritoPrograma.usuario_id == usuario.id)
        .all()
    )

    favoritos_ids = {p.id for p in programas}

    return [montar_response(p, favoritos_ids) for p in programas]


#LISTAR PROGRAMAS

@programa_router.get("/")
async def listar_programas(
    area: Optional[str] = Query(None),
    uf: Optional[str] = Query(None),
    nivel: Optional[str] = Query(None),
    nota_min: Optional[int] = Query(None, ge=1, le=7),
    regiao: Optional[str] = Query(None),
    ies: Optional[str] = Query(None),
    publica: Optional[bool] = Query(None),
    busca: Optional[str] = Query(None),

    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),

    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    query = (
        session.query(Programa)
        .options(joinedload(Programa.cursos), joinedload(Programa.linhas_pesquisa))
        .filter(Programa.situacao == "ATIVO")
    )

    if area:
        query = query.filter(
            or_(
                Programa.area_conhecimento.ilike(f"%{area}%"),
                Programa.area_avaliacao.ilike(f"%{area}%"),
                Programa.grande_area.ilike(f"%{area}%"),
            )
        )

    if uf:
        query = query.filter(Programa.uf.ilike(uf.strip()))

    if nivel:
        query = query.join(Curso).filter(
            Curso.nivel == nivel.upper(),
            Curso.situacao == "ATIVO",
        )

    if nota_min:
        query = query.filter(Programa.nota >= nota_min)

    if regiao:
        query = query.filter(Programa.regiao.ilike(f"%{regiao}%"))

    if ies:
        query = query.filter(
            or_(
                Programa.nome_ies.ilike(f"%{ies}%"),
                Programa.sigla_ies.ilike(f"%{ies}%"),
            )
        )

    if publica is not None:
        termo = "pública" if publica else "privada"
        query = query.filter(Programa.categoria_ies.ilike(f"%{termo}%"))

    if busca:
        query = query.filter(
            or_(
                Programa.nome.ilike(f"%{busca}%"),
                Programa.nome_ies.ilike(f"%{busca}%"),
                Programa.sigla.ilike(f"%{busca}%"),
            )
        )

    total = query.count()

    query = query.order_by(Programa.nota.desc().nullslast(), Programa.nome.asc())

    programas = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    #OTIMIZAÇÃO (uma query só)
    favoritos_ids = {
        f.programa_id
        for f in session.query(FavoritoPrograma)
        .filter(FavoritoPrograma.usuario_id == usuario.id)
        .all()
    }

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "programas": [montar_response(p, favoritos_ids) for p in programas],
    }


#DETALHE

@programa_router.get("/{programa_id}")
async def detalhe_programa(
    programa_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    programa = (
        session.query(Programa)
        .options(joinedload(Programa.cursos), joinedload(Programa.linhas_pesquisa))
        .filter(Programa.id == programa_id)
        .first()
    )

    if not programa:
        raise HTTPException(status_code=404, detail="Programa não encontrado")

    favoritos_ids = {
        f.programa_id
        for f in session.query(FavoritoPrograma)
        .filter(FavoritoPrograma.usuario_id == usuario.id)
        .all()
    }

    return montar_response(programa, favoritos_ids)


#FAVORITAR

@programa_router.post("/{programa_id}/favoritar")
async def favoritar_programa(
    programa_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    programa = session.query(Programa).filter(Programa.id == programa_id).first()

    if not programa:
        raise HTTPException(status_code=404, detail="Programa não encontrado")

    ja_favoritado = session.query(FavoritoPrograma).filter(
        FavoritoPrograma.usuario_id == usuario.id,
        FavoritoPrograma.programa_id == programa_id,
    ).first()

    if ja_favoritado:
        raise HTTPException(
            status_code=400,
            detail="Você já favoritou este programa"
        )

    favorito = FavoritoPrograma(usuario_id=usuario.id, programa_id=programa_id)
    session.add(favorito)
    session.commit()

    return {"msg": "Programa adicionado aos favoritos"}


#DESFAVORITAR

@programa_router.delete("/{programa_id}/favoritar")
async def desfavoritar_programa(
    programa_id: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    favorito = session.query(FavoritoPrograma).filter(
        FavoritoPrograma.usuario_id == usuario.id,
        FavoritoPrograma.programa_id == programa_id,
    ).first()

    if not favorito:
        raise HTTPException(status_code=404, detail="Programa não está nos favoritos")

    session.delete(favorito)
    session.commit()

    return {"msg": "Programa removido dos favoritos"}


#FILTROS   

@programa_router.get("/filtros/opcoes")
async def opcoes_de_filtro(
    session: Session = Depends(pegar_sessao),
    _: Usuario = Depends(verificar_token),
):
    ufs = session.query(Programa.uf).filter(Programa.uf.isnot(None)).distinct().all()
    areas = session.query(Programa.area_conhecimento).filter(Programa.area_conhecimento.isnot(None)).distinct().all()
    grandes_areas = session.query(Programa.grande_area).filter(Programa.grande_area.isnot(None)).distinct().all()

    return {
        "ufs": [r[0] for r in ufs],
        "areas": [r[0] for r in areas],
        "grandes_areas": [r[0] for r in grandes_areas],
        "niveis": [
            {"codigo": "M", "label": "Mestrado Acadêmico"},
            {"codigo": "F", "label": "Mestrado Profissional"},
            {"codigo": "D", "label": "Doutorado"},
        ],
        "notas": list(range(1, 8)),
    }