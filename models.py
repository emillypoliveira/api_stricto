from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id        = Column(Integer, primary_key=True, index=True)
    nome      = Column(String, nullable=False)
    email     = Column(String, unique=True, nullable=False, index=True)
    senha     = Column(String, nullable=False)
    role      = Column(String, nullable=False)  # estudante ou coordenador
    foto_url  = Column(String, nullable=True)

    # Relacionamentos
    seletivos_criados  = relationship("Seletivo", back_populates="coordenador")
    favoritos          = relationship("Favorito", back_populates="usuario")
    notificacoes       = relationship("Notificacao", back_populates="usuario")
    tokens_recuperacao = relationship("TokenRecuperacao", back_populates="usuario")


class Seletivo(Base):
    __tablename__ = "seletivos"

    id             = Column(Integer, primary_key=True, index=True)
    titulo         = Column(String, nullable=False)
    descricao      = Column(Text, nullable=False)
    area           = Column(String, nullable=True)
    data_inicio    = Column(DateTime(timezone=True), nullable=False)
    data_fim       = Column(DateTime(timezone=True), nullable=False)
    link_inscricao = Column(String, nullable=True)
    bolsa_valor    = Column(Float, nullable=True)
    nivel          = Column(String, nullable=True)
    coordenador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    criado_em      = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    coordenador  = relationship("Usuario", back_populates="seletivos_criados")
    favoritos    = relationship("Favorito", back_populates="seletivo")
    notificacoes = relationship("Notificacao", back_populates="seletivo")


class Favorito(Base):
    __tablename__ = "favoritos"

    id          = Column(Integer, primary_key=True, index=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    seletivo_id = Column(Integer, ForeignKey("seletivos.id"), nullable=False)

    # Relacionamentos
    usuario  = relationship("Usuario", back_populates="favoritos")
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

    # Relacionamentos
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

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="tokens_recuperacao")
