from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta, timezone

from models import Usuario
from schemas import UsuarioCreateSchema, LoginSchema
from dependencies import pegar_sessao, verificar_token
from security import SECRET_KEY, ALGORITHM, hash_senha, verificar_senha, ACCESS_TOKEN_EXPIRE_MINUTES

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


# CRIAR TOKEN

def criar_token(usuario: Usuario, duracao_token: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    data_expiracao = datetime.now(timezone.utc) + duracao_token
    
    payload = {
        "sub": str(usuario.id),
        "role": usuario.role,   #importante
        "exp": data_expiracao
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



# AUTENTICAR USUÁRIO

def autenticar_usuario(email: str, senha: str, session: Session):
    usuario = session.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        return None

    if not verificar_senha(senha, usuario.senha):
        return None

    return usuario


# ROTA TESTE

@auth_router.get("/")
async def home():
    return {"mensagem": "Rota de autenticação funcionando!"}



# CRIAR CONTA

@auth_router.post("/criar_conta")
async def criar_conta(usuario_schema: UsuarioCreateSchema, session: Session = Depends(pegar_sessao)):

    usuario_existente = session.query(Usuario).filter(Usuario.email == usuario_schema.email).first()

    if usuario_existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    senha_criptografada = hash_senha(usuario_schema.senha)

    novo_usuario = Usuario(
        nome=usuario_schema.nome,
        email=usuario_schema.email,
        senha=senha_criptografada,
        role=usuario_schema.role  #  estudante ou coordenador
    )

    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)

    return {"msg": "Usuário criado com sucesso"}


# LOGIN (JSON)

@auth_router.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(pegar_sessao)):

    usuario = autenticar_usuario(login_schema.email, login_schema.senha, session)

    if not usuario:
        raise HTTPException(status_code=400, detail="Credenciais inválidas")

    access_token = criar_token(usuario)
    refresh_token = criar_token(usuario, duracao_token=timedelta(days=7))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }

# LOGIN FORM (Swagger)

@auth_router.post("/login-form")
async def login_form(
    dados_formulario: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(pegar_sessao)
):

    usuario = autenticar_usuario(dados_formulario.username, dados_formulario.password, session)

    if not usuario:
        raise HTTPException(status_code=400, detail="Credenciais inválidas")

    access_token = criar_token(usuario)

    return {"access_token": access_token, "token_type": "Bearer"}


# REFRESH TOKEN

@auth_router.get("/refresh")
async def refresh_token(usuario: Usuario = Depends(verificar_token)):
    access_token = criar_token(usuario)

    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }


# USUÁRIO LOGADO

@auth_router.get("/me")
async def perfil(usuario: Usuario = Depends(verificar_token)):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "role": usuario.role
    }