from fastapi import Depends, HTTPException, WebSocket, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from jose import jwt, JWTError
from security import SECRET_KEY, ALGORITHM
from models import Usuario
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")



# SESSÃO DB

def pegar_sessao():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TOKEN NORMAL (ACCESS)

def verificar_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(pegar_sessao),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token inválido")

        user_id = payload.get("sub")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return usuario



# TOKEN REFRESH

def verificar_refresh_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(pegar_sessao),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")

        user_id = payload.get("sub")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return usuario



# WEBSOCKET

async def verificar_token_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(pegar_sessao),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            await websocket.close(code=1008)
            raise HTTPException(status_code=401)

    except JWTError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401)

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()

    if not usuario:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401)

    return usuario



# PERMISSÃO

def apenas_coordenador(usuario: Usuario = Depends(verificar_token)):
    if usuario.role != "coordenador":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return usuario