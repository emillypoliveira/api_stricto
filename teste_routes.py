from fastapi import APIRouter
from email_service import enviar_email_verificacao

teste_router = APIRouter()


@teste_router.get("/teste-email")
async def teste_email():

    sucesso = await enviar_email_verificacao(
        destinatario="emilly.oliveira81900@gmail.com",
        nome="Emilly",
        token_raw="Clique para confirmar"
    )

    return {
        "sucesso": sucesso
    }