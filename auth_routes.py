from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta, timezone

from models import Usuario
from schemas import UsuarioCreateSchema, LoginSchema
from dependencies import pegar_sessao, verificar_token, verificar_refresh_token
from security import SECRET_KEY, ALGORITHM, hash_senha, verificar_senha, ACCESS_TOKEN_EXPIRE_MINUTES

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


# ─────────────────────────────────────────────
# 🔐 CRIAR TOKEN (ACCESS / REFRESH)
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
        "type": tipo,  # 👈 diferencia access e refresh
        "exp": datetime.now(timezone.utc) + duracao_token
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ─────────────────────────────────────────────
# 👤 AUTENTICAR USUÁRIO
# ─────────────────────────────────────────────

def autenticar_usuario(email: str, senha: str, session: Session):
    usuario = session.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        return None

    if not verificar_senha(senha, usuario.senha):
        return None

    return usuario


# ─────────────────────────────────────────────
# 🏠 TESTE
# ─────────────────────────────────────────────

@auth_router.get("/")
async def home():
    return {"mensagem": "Auth funcionando"}


# ─────────────────────────────────────────────
# 📝 CRIAR CONTA
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

    novo_usuario = Usuario(
        nome=usuario_schema.nome,
        email=usuario_schema.email,
        senha=senha_criptografada,
        role=usuario_schema.role.value
    )

    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)

    return {"mensagem": "Usuário criado com sucesso"}


# ─────────────────────────────────────────────
# 🔑 LOGIN JSON
# ─────────────────────────────────────────────

@auth_router.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(pegar_sessao)):

    usuario = autenticar_usuario(login_schema.email, login_schema.senha, session)

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token = criar_token(usuario, tipo="access")
    refresh_token = criar_token(usuario, tipo="refresh")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }


# ─────────────────────────────────────────────
# 🔑 LOGIN FORM (Swagger)
# ─────────────────────────────────────────────

@auth_router.post("/login-form")
async def login_form(
    dados: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(pegar_sessao)
):

    usuario = autenticar_usuario(dados.username, dados.password, session)

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token = criar_token(usuario, tipo="access")

    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }


# ─────────────────────────────────────────────
# 🔄 REFRESH TOKEN (CORRETO)
# ─────────────────────────────────────────────

@auth_router.post("/refresh")
async def refresh(usuario: Usuario = Depends(verificar_refresh_token)):

    access_token = criar_token(usuario, tipo="access")

    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }


# ─────────────────────────────────────────────
# 👤 USUÁRIO LOGADO
# ─────────────────────────────────────────────

@auth_router.get("/me")
async def perfil(usuario: Usuario = Depends(verificar_token)):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "role": usuario.role
    }