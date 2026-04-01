from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from jose import jwt, JWTError
from security import SECRET_KEY, ALGORITHM
from models import Usuario
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")


# sessão do banco
def pegar_sessao():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# verificar token
def verificar_token(token: str = Depends(oauth2_scheme), db: Session = Depends(pegar_sessao)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return usuario


# 🔒 permissão coordenador
def apenas_coordenador(usuario: Usuario = Depends(verificar_token)):
    if usuario.role != "coordenador":
        raise HTTPException(status_code=403, detail="Acesso negado")

    return usuario 