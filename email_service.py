import os
import resend
from fastapi.concurrency import run_in_threadpool # Importante para não travar o app

resend.api_key = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "onboarding@resend.dev") # Padrão para testes

def _html(titulo: str, mensagem: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head><meta charset="UTF-8" /></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
      <div style="max-width:600px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <div style="background:#4F46E5;color:#fff;padding:24px;font-size:20px;font-weight:bold;">
          {titulo}
        </div>
        <div style="padding:24px;color:#333;font-size:15px;line-height:1.6;">
          {mensagem.replace('\n', '<br>')}
        </div>
        <div style="padding:16px 24px;font-size:12px;color:#999;background:#f9f9f9;">
          Você recebeu esta notificação porque se cadastrou para atualizações acadêmicas.
        </div>
      </div>
    </body>
    </html>
    """

async def enviar_email_notificacao(
    destinatario: str,
    titulo: str,
    mensagem: str,
) -> bool:
    try:
        # Usamos run_in_threadpool porque o resend.Emails.send é bloqueante
        params = {
            "from": EMAIL_FROM,
            "to": [destinatario],
            "subject": titulo,
            "html": _html(titulo, mensagem),
            "text": mensagem,
        }
        
        await run_in_threadpool(resend.Emails.send, params)
        return True
    except Exception as e:
        print(f"[RESEND ERROR] {e}")
        return False
