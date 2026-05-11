from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ── Usuário / Auth ──────────────────────

class RoleEnum(str, Enum):
    estudante = "estudante"
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

    # Campos do coordenador
    cpf: Optional[str] = None
    celular: Optional[str] = None
    area: Optional[str] = None
    subarea: Optional[str] = None
    instituicao: Optional[str] = None

    # Validação de documento
    documento_url: Optional[str] = None
    documento_nome: Optional[str] = None
    status_validacao: Optional[str] = None
    validacao_mensagem: Optional[str] = None
    validado_em: Optional[datetime] = None
    criado_em: Optional[datetime] = None
    email_institucional: Optional[str] = None
    titulacao: Optional[str] = None

    class Config:
        from_attributes = True



class AtualizarPerfilSchema(BaseModel):
    nome: Optional[str] = None
    foto_url: Optional[str] = None

    # Campos do coordenador
    cpf: Optional[str] = None
    celular: Optional[str] = None
    area: Optional[str] = None
    subarea: Optional[str] = None
    instituicao: Optional[str] = None

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


# ── Seletivo ───────────────────

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
    subarea: Optional[str] = None          # novo
    data_inicio: datetime
    data_fim: datetime
    data_prova: Optional[datetime] = None  # novo
    link_inscricao: Optional[str] = None
    bolsa_valor: Optional[float] = None
    nivel: Optional[str] = None
    favoritos: Optional[int] = 0           # novo
    nota_capes: Optional[int] = None       # novo
    coordenador_id: int
    coordenador_nome: Optional[str] = None
    favoritado: Optional[bool] = False
    criado_em: datetime
    etapas: List[EtapaResponse] = []       # novo
    editais: List[EditalResponse] = []     # novo

    class Config:
        from_attributes = True


# ── Etapa ──────────────────────────────────────────────────────────────────────

class EtapaResponse(BaseModel):
    id: int
    ordem: int
    descricao: str

    class Config:
        from_attributes = True


# ── Documento Edital ───────────────────────────────────────────────────────────

class DocumentoEditalCreate(BaseModel):
    titulo: str
    url_arquivo: Optional[str] = None
    url_externo: Optional[str] = None
    is_pdf: bool = False

class DocumentoEditalResponse(BaseModel):
    id: int
    titulo: str
    url_arquivo: Optional[str] = None
    url_externo: Optional[str] = None
    is_pdf: bool

    class Config:
        from_attributes = True


# ── Edital ─────────────────────────────────────────────────────────────────────

class EditalCreate(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    vagas: Optional[int] = None
    data_inicio_inscricao: Optional[datetime] = None
    data_fim_inscricao: Optional[datetime] = None
    data_prova: Optional[datetime] = None
    documentos: List[DocumentoEditalCreate] = []

class EditalResponse(BaseModel):
    id: int
    seletivo_id: int
    titulo: str
    descricao: Optional[str] = None
    vagas: Optional[int] = None
    data_inicio_inscricao: Optional[datetime] = None
    data_fim_inscricao: Optional[datetime] = None
    data_prova: Optional[datetime] = None
    criado_em: datetime
    documentos: List[DocumentoEditalResponse] = []

    class Config:
        from_attributes = True

# ── Notificação ─────────────────────

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


# ── Programa ─────────────────

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



class CompletarPerfilEstudanteSchema(BaseModel):
    nome: str
    cpf: str
    celular: str
    titulacao: Optional[str] = None
    area: Optional[str] = None

class CompletarPerfilCoordenadorSchema(BaseModel):
    nome: str
    cpf: str
    celular: str
    email_institucional: Optional[str] = None
    area: Optional[str] = None
    subarea: Optional[str] = None
    instituicao: Optional[str] = None