from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Usuário / Auth ─────────────────────────────────────────────────────────────

class UsuarioCreateSchema(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    role: str  # estudante ou coordenador


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

class NotificacaoResponse(BaseModel):
    id: int
    titulo: str
    mensagem: str
    lida: bool
    criado_em: datetime
    seletivo_id: Optional[int] = None

    class Config:
        from_attributes = True
