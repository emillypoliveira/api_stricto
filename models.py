from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id        = Column(Integer, primary_key=True, index=True)
    nome      = Column(String, nullable=False)
    email     = Column(String, unique=True, nullable=False, index=True)
    senha     = Column(String, nullable=False)
    role      = Column(String, nullable=False)
    foto_url  = Column(String, nullable=True)

    # Verificação de e-mail
    email_verificado  = Column(Boolean, default=False)
    token_verificacao = Column(String, nullable=True)
    token_expira_em   = Column(DateTime(timezone=True), nullable=True)

    # Campos do coordenador
    cpf         = Column(String, nullable=True)
    celular     = Column(String, nullable=True)
    area        = Column(String, nullable=True)
    subarea     = Column(String, nullable=True)
    instituicao = Column(String, nullable=True)

    # Validação de documento
    documento_url      = Column(String, nullable=True)
    documento_nome     = Column(String, nullable=True)
    status_validacao   = Column(String, nullable=True)
    validacao_mensagem = Column(String, nullable=True)
    validado_em        = Column(DateTime(timezone=True), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos (sem alteração)
    seletivos_criados  = relationship("Seletivo", back_populates="coordenador")
    favoritos          = relationship("Favorito", back_populates="usuario")
    notificacoes       = relationship("Notificacao", back_populates="usuario")
    tokens_recuperacao = relationship("TokenRecuperacao", back_populates="usuario")
    favoritos_programa = relationship(
        "FavoritoPrograma",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )

class Seletivo(Base):
    __tablename__ = "seletivos"

    id             = Column(Integer, primary_key=True, index=True)
    titulo         = Column(String, nullable=False)
    descricao      = Column(Text, nullable=False)
    area           = Column(String, nullable=True)
    subarea        = Column(String, nullable=True)        # novo
    data_inicio    = Column(DateTime(timezone=True), nullable=False)
    data_fim       = Column(DateTime(timezone=True), nullable=False)
    data_prova     = Column(DateTime(timezone=True), nullable=True)  # novo
    link_inscricao = Column(String, nullable=True)
    bolsa_valor    = Column(Float, nullable=True)
    nivel          = Column(String, nullable=True)
    favoritos      = Column(Integer, default=0)           # novo
    nota_capes     = Column(Integer, nullable=True)       # novo
    coordenador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    criado_em      = Column(DateTime(timezone=True), server_default=func.now())

    coordenador  = relationship("Usuario", back_populates="seletivos_criados")
    notificacoes = relationship("Notificacao", back_populates="seletivo")
    etapas       = relationship("EtapaSeletivo", back_populates="seletivo", cascade="all, delete-orphan")
    editais      = relationship("Edital", back_populates="seletivo", cascade="all, delete-orphan")

    favoritos = relationship("Favorito", back_populates="seletivo")


class EtapaSeletivo(Base):
    __tablename__ = "etapas_seletivo"

    id          = Column(Integer, primary_key=True, index=True)
    seletivo_id = Column(Integer, ForeignKey("seletivos.id"), nullable=False)
    ordem       = Column(Integer, nullable=False)
    descricao   = Column(Text, nullable=False)

    seletivo = relationship("Seletivo", back_populates="etapas")


class Edital(Base):
    __tablename__ = "editais"

    id                   = Column(Integer, primary_key=True, index=True)
    seletivo_id          = Column(Integer, ForeignKey("seletivos.id"), nullable=False)
    titulo               = Column(String, nullable=False)
    descricao            = Column(Text, nullable=True)
    vagas                = Column(Integer, nullable=True)
    data_inicio_inscricao = Column(DateTime(timezone=True), nullable=True)
    data_fim_inscricao   = Column(DateTime(timezone=True), nullable=True)
    data_prova           = Column(DateTime(timezone=True), nullable=True)
    criado_em            = Column(DateTime(timezone=True), server_default=func.now())

    seletivo   = relationship("Seletivo", back_populates="editais")
    documentos = relationship("DocumentoEdital", back_populates="edital", cascade="all, delete-orphan")


class DocumentoEdital(Base):
    __tablename__ = "documentos_edital"

    id          = Column(Integer, primary_key=True, index=True)
    edital_id   = Column(Integer, ForeignKey("editais.id"), nullable=False)
    titulo      = Column(String, nullable=False)
    url_arquivo = Column(String, nullable=True)
    url_externo = Column(String, nullable=True)
    is_pdf      = Column(Boolean, default=False)

    edital = relationship("Edital", back_populates="documentos")


class Favorito(Base):
    __tablename__ = "favoritos"

    id          = Column(Integer, primary_key=True, index=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    seletivo_id = Column(Integer, ForeignKey("seletivos.id"), nullable=False)

    usuario  = relationship("Usuario", back_populates="favoritos")
    seletivo = relationship("Seletivo", back_populates="favoritos")

    seletivo = relationship("Seletivo", back_populates="favoritos")


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id          = Column(Integer, primary_key=True, index=True)
    titulo      = Column(String, nullable=False)
    mensagem    = Column(Text, nullable=False)
    lida        = Column(Boolean, default=False)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    seletivo_id = Column(Integer, ForeignKey("seletivos.id"), nullable=True)
    criado_em   = Column(DateTime(timezone=True), server_default=func.now())

    usuario  = relationship("Usuario", back_populates="notificacoes")
    seletivo = relationship("Seletivo", back_populates="notificacoes")


class TokenRecuperacao(Base):
    __tablename__ = "tokens_recuperacao"

    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token      = Column(String, unique=True, nullable=False)
    usado      = Column(Boolean, default=False)
    expira_em  = Column(DateTime(timezone=True), nullable=False)
    criado_em  = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="tokens_recuperacao")


class Programa(Base):
    __tablename__ = "programas"

    id                = Column(Integer, primary_key=True, index=True)
    codigo_capes      = Column(String, unique=True, nullable=True, index=True)
    nome              = Column(String, nullable=False, index=True)
    sigla             = Column(String, nullable=True)
    situacao          = Column(String, nullable=True)

    nome_ies          = Column(String, nullable=True)
    sigla_ies         = Column(String, nullable=True)
    categoria_ies     = Column(String, nullable=True)

    uf                = Column(String(2), nullable=True, index=True)
    municipio         = Column(String, nullable=True)
    regiao            = Column(String, nullable=True)

    grande_area       = Column(String, nullable=True)
    area_conhecimento = Column(String, nullable=True, index=True)
    area_avaliacao    = Column(String, nullable=True)
    area_basica       = Column(String, nullable=True)

    nota              = Column(Integer, nullable=True)
    ano_inicio        = Column(Integer, nullable=True)

    criado_em         = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em     = Column(DateTime(timezone=True), onupdate=func.now())

    cursos = relationship("Curso", back_populates="programa", cascade="all, delete-orphan")

    linhas_pesquisa = relationship("LinhaPesquisa", back_populates="programa", cascade="all, delete-orphan")

    favoritos_programa = relationship(
        "FavoritoPrograma",
        back_populates="programa",
        cascade="all, delete-orphan"
    )


class Curso(Base):
    __tablename__ = "cursos"

    id            = Column(Integer, primary_key=True, index=True)
    programa_id   = Column(Integer, ForeignKey("programas.id"), nullable=False)
    nivel         = Column(String, nullable=False, index=True)
    nivel_label   = Column(String, nullable=True)
    situacao      = Column(String, nullable=True)
    ano_inicio    = Column(Integer, nullable=True)

    programa = relationship("Programa", back_populates="cursos")


class LinhaPesquisa(Base):
    __tablename__ = "linhas_pesquisa"

    id          = Column(Integer, primary_key=True, index=True)
    programa_id = Column(Integer, ForeignKey("programas.id"), nullable=False)
    descricao   = Column(Text, nullable=False)  # ✅ corrigido

    programa = relationship("Programa", back_populates="linhas_pesquisa")


class FavoritoPrograma(Base):
    __tablename__ = "favoritos_programa"

    id          = Column(Integer, primary_key=True, index=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    programa_id = Column(Integer, ForeignKey("programas.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("usuario_id", "programa_id", name="uq_usuario_programa"),
    )

    usuario  = relationship("Usuario", back_populates="favoritos_programa")
    programa = relationship("Programa", back_populates="favoritos_programa")
