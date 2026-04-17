from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ── Usuário / Auth ─────────────────────────────────────────────────────────────

class RoleEnum(str, Enum):
    aluno = "aluno"
    coordenador = "coordenador"


class UsuarioCreateSchema(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    role: RoleEnum

    @field_validator("nome")
    def nome_completo(cls, value):
        if len(value.strip().split(" ")) < 2:
            raise ValueError("Informe nome e sobrenome")
        return value


class LoginSchema(BaseModel):
    email: EmailStr
    senha: str


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    role: str
    foto_url: Optional[str] = None

    class Config:
        from_attributes = True


class AtualizarPerfilSchema(BaseModel):
    nome: Optional[str] = None
    foto_url: Optional[str] = None

    @field_validator("nome")
    def nome_completo(cls, value):
        if value and len(value.strip().split(" ")) < 2:
            raise ValueError("Informe nome e sobrenome")
        return value


class RecuperarSenhaSchema(BaseModel):
    email: EmailStr


class AlterarSenhaSchema(BaseModel):
    token: str
    nova_senha: str


# ── Seletivo ───────────────────────────────────────────────────────────────────

class SeletivoCreateSchema(BaseModel):
    titulo: str
    descricao: str
    area: Optional[str] = None
    data_inicio: datetime
    data_fim: datetime
    link_inscricao: Optional[str] = None
    bolsa_valor: Optional[float] = None
    nivel: Optional[str] = None


class SeletivoUpdateSchema(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    area: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    link_inscricao: Optional[str] = None
    bolsa_valor: Optional[float] = None
    nivel: Optional[str] = None


class SeletivoResponse(BaseModel):
    id: int
    titulo: str
    descricao: str
    area: Optional[str] = None
    data_inicio: datetime
    data_fim: datetime
    link_inscricao: Optional[str] = None
    bolsa_valor: Optional[float] = None
    nivel: Optional[str] = None
    coordenador_id: int
    coordenador_nome: Optional[str] = None
    favoritado: Optional[bool] = False
    criado_em: datetime

    class Config:
        from_attributes = True


# ── Notificação ────────────────────────────────────────────────────────────────

# NOVO: usado para criar notificações via POST /notificacoes/
class NotificacaoCreate(BaseModel):
    usuario_id: int
    titulo: str
    mensagem: str
    tipo: str = "geral"        # "alerta" | "info" | "sucesso" | "geral"
    enviar_email: bool = True


class NotificacaoResponse(BaseModel):
    id: int
    titulo: str
    mensagem: str
    lida: bool
    criado_em: datetime
    seletivo_id: Optional[int] = None
    tipo: Optional[str] = "geral"   # NOVO

    class Config:
        from_attributes = True


# ── Programa ───────────────────────────────────────────────────────────────────

class ProgramaResponse(BaseModel):
    id: int
    nome: str
    sigla: Optional[str] = None
    nome_ies: Optional[str] = None
    uf: Optional[str] = None
    area_conhecimento: Optional[str] = None
    nota: Optional[int] = None

    class Config:
        from_attributes = True


class CursoResponse(BaseModel):
    id: int
    nivel: str
    nivel_label: Optional[str] = None

    class Config:
        from_attributes = True


class LinhaPesquisaResponse(BaseModel):
    id: int
    descricao: str

    class Config:
        from_attributes = True


class ProgramaDetalheResponse(BaseModel):
    id: int
    nome: str
    sigla: Optional[str] = None
    nome_ies: Optional[str] = None
    uf: Optional[str] = None
    area_conhecimento: Optional[str] = None
    nota: Optional[int] = None
    cursos: List[CursoResponse] = []
    linhas_pesquisa: List[LinhaPesquisaResponse] = []

    class Config:
        from_attributes = True