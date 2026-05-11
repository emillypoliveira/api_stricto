
Copiar

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta, timezone
import hashlib
 
from models import Usuario
from schemas import UsuarioCreateSchema, LoginSchema, CompletarPerfilEstudanteSchema, CompletarPerfilCoordenadorSchema, UsuarioResponse
from dependencies import pegar_sessao, verificar_token, verificar_refresh_token
from security import SECRET_KEY, ALGORITHM, hash_senha, verificar_senha, ACCESS_TOKEN_EXPIRE_MINUTES
from auth_utils import gerar_token_verificacao
from email_service import enviar_email_verificacao
 
auth_router = APIRouter(prefix="/auth", tags=["Auth"])
 
 
# ─────────────────────────────────────────────
# CRIAR TOKEN (ACCESS / REFRESH)
# ─────────────────────────────────────────────
 
def criar_token(usuario: Usuario, tipo: str = "access", duracao_token: timedelta = None):
    if not duracao_token:
        if tipo == "access":
            duracao_token = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            duracao_token = timedelta(days=7)
 
    payload = {
        "sub": str(usuario.id),
        "role": usuario.role,
        "type": tipo,
        "exp": datetime.now(timezone.utc) + duracao_token
    }
 
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
 
 
# ─────────────────────────────────────────────
# AUTENTICAR USUÁRIO
# ─────────────────────────────────────────────
 
def autenticar_usuario(email: str, senha: str, session: Session):
    usuario = session.query(Usuario).filter(Usuario.email == email).first()
 
    if not usuario:
        return None
 
    if not verificar_senha(senha, usuario.senha):
        return None
 
    return usuario
 
 
# ─────────────────────────────────────────────
# TESTE
# ─────────────────────────────────────────────
 
@auth_router.get("/")
async def home():
    return {"mensagem": "Auth funcionando"}
 
 
# ─────────────────────────────────────────────
# CRIAR CONTA
# ─────────────────────────────────────────────
 
@auth_router.post("/criar_conta")
async def criar_conta(
    usuario_schema: UsuarioCreateSchema,
    session: Session = Depends(pegar_sessao)
):
    usuario_existente = session.query(Usuario).filter(
        Usuario.email == usuario_schema.email
    ).first()
 
    if usuario_existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
 
    senha_criptografada = hash_senha(usuario_schema.senha)
 
    # Gera token de verificação
    token_raw, token_hash, expira_em = gerar_token_verificacao()
 
    novo_usuario = Usuario(
        nome=usuario_schema.nome,
        email=usuario_schema.email,
        senha=senha_criptografada,
        role=usuario_schema.role.value,
        email_verificado=False,
        token_verificacao=token_hash,      # salva o HASH no banco
        token_expira_em=expira_em,
    )
 
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
 
    # Envia o email com o token RAW (não o hash)
    await enviar_email_verificacao(novo_usuario.email, novo_usuario.nome, token_raw)
 
    return {
        "mensagem": "Usuário criado com sucesso. Verifique seu e-mail para ativar a conta.",
        "email_verificado": False,
    }
 
 
# ─────────────────────────────────────────────
# VERIFICAR EMAIL (via link ou app)
# ─────────────────────────────────────────────
 
@auth_router.get("/verificar-email")
async def verificar_email(
    token: str = Query(..., description="Token recebido por e-mail"),
    session: Session = Depends(pegar_sessao)
):
    # Faz o hash do token recebido para comparar com o banco
    token_hash = hashlib.sha256(token.encode()).hexdigest()
 
    usuario = session.query(Usuario).filter(
        Usuario.token_verificacao == token_hash
    ).first()
 
    if not usuario:
        raise HTTPException(status_code=400, detail="Token inválido")
 
    # Verifica expiração (converte para timezone-aware se necessário)
    expira_em = usuario.token_expira_em
    agora = datetime.now(timezone.utc)
 
    if expira_em.tzinfo is None:
        # Se o banco salvou sem timezone, compara sem timezone
        agora = datetime.utcnow()
 
    if agora > expira_em:
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo e-mail de verificação.")
 
    # Marca como verificado e limpa o token
    usuario.email_verificado = True
    usuario.token_verificacao = None
    usuario.token_expira_em = None
 
    session.commit()
 
    return {"mensagem": "E-mail verificado com sucesso! Você já pode fazer login."}
 
 
# ─────────────────────────────────────────────
# REENVIAR EMAIL DE VERIFICAÇÃO
# ─────────────────────────────────────────────
 
@auth_router.post("/reenviar-verificacao")
async def reenviar_verificacao(
    email: str = Query(...),
    session: Session = Depends(pegar_sessao)
):
    usuario = session.query(Usuario).filter(Usuario.email == email).first()
 
    if not usuario:
        # Não revela se o email existe ou não (segurança)
        return {"mensagem": "Se o e-mail estiver cadastrado, você receberá um novo link."}
 
    if usuario.email_verificado:
        raise HTTPException(status_code=400, detail="E-mail já verificado.")
 
    token_raw, token_hash, expira_em = gerar_token_verificacao()
 
    usuario.token_verificacao = token_hash
    usuario.token_expira_em = expira_em
 
    session.commit()
 
    await enviar_email_verificacao(usuario.email, usuario.nome, token_raw)
 
    return {"mensagem": "Se o e-mail estiver cadastrado, você receberá um novo link."}
 
 
# ─────────────────────────────────────────────
# LOGIN JSON
# ─────────────────────────────────────────────
 
@auth_router.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(pegar_sessao)):
 
    usuario = autenticar_usuario(login_schema.email, login_schema.senha, session)
 
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
 
    # Bloqueia login se email não verificado
    if not usuario.email_verificado:
        raise HTTPException(
            status_code=403,
            detail="E-mail não verificado. Verifique sua caixa de entrada.",
        )
 
    access_token = criar_token(usuario, tipo="access")
    refresh_token = criar_token(usuario, tipo="refresh")
 
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "role": usuario.role,
        "email_verificado": usuario.email_verificado,
    }
 
 
# ─────────────────────────────────────────────
# LOGIN FORM (Swagger)
# ─────────────────────────────────────────────
 
@auth_router.post("/login-form")
async def login_form(
    dados: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(pegar_sessao)
):
    usuario = autenticar_usuario(dados.username, dados.password, session)
 
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
 
    if not usuario.email_verificado:
        raise HTTPException(status_code=403, detail="E-mail não verificado.")
 
    access_token = criar_token(usuario, tipo="access")
 
    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }
 
 
# ─────────────────────────────────────────────
# REFRESH TOKEN
# ─────────────────────────────────────────────
 
@auth_router.post("/refresh")
async def refresh(usuario: Usuario = Depends(verificar_refresh_token)):
    access_token = criar_token(usuario, tipo="access")
 
    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }
 
 
# ─────────────────────────────────────────────
# USUÁRIO LOGADO
# ─────────────────────────────────────────────
 
@auth_router.get("/me")
async def perfil(usuario: Usuario = Depends(verificar_token)):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "role": usuario.role,
        "email_verificado": usuario.email_verificado,
    }
 
 
# ─────────────────────────────────────────────
# COMPLETAR PERFIL (ONBOARDING)
# ─────────────────────────────────────────────
 
@auth_router.patch("/completar-perfil")
async def completar_perfil(
    dados: dict,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token),
):
    if usuario.role == "coordenador":
        schema = CompletarPerfilCoordenadorSchema(**dados)
    else:
        schema = CompletarPerfilEstudanteSchema(**dados)
 
    campos = schema.model_dump(exclude_none=True)
    for campo, valor in campos.items():
        setattr(usuario, campo, valor)
 
    session.commit()
    session.refresh(usuario)
    return UsuarioResponse.model_validate(usuario)