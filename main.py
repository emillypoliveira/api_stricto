from fastapi import FastAPI
from database import engine, Base
from auth_routes import auth_router
from seletivo_routes import seletivo_router, coordenador_router
from notificacao_routes import notificacao_router 
from programa_routes import programa_router

# cria tabelas no banco
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Stricto")

# rotas
app.include_router(auth_router)
app.include_router(seletivo_router)
app.include_router(coordenador_router)
app.include_router(notificacao_router)
app.include_router(programa_router)  


@app.get("/")
def home():
    return {"msg": "API rodando "}