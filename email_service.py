import os
import resend
from fastapi.concurrency import run_in_threadpool
 
resend.api_key = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # URL da sua API
 
 
# ─────────────────────────────────────────────
# TEMPLATE HTML GENÉRICO
# ─────────────────────────────────────────────
 
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
          {mensagem.replace(chr(10), '<br>')}
        </div>
        <div style="padding:16px 24px;font-size:12px;color:#999;background:#f9f9f9;">
          Você recebeu esta notificação porque se cadastrou para atualizações acadêmicas.
        </div>
      </div>
    </body>
    </html>
    """
 
 
# ─────────────────────────────────────────────
# TEMPLATE HTML DE VERIFICAÇÃO (com botão)
# ─────────────────────────────────────────────
 
def _html_verificacao(nome: str, link: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head><meta charset="UTF-8" /></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
      <div style="max-width:600px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <div style="background:#4F46E5;color:#fff;padding:24px;font-size:20px;font-weight:bold;">
          Confirme seu e-mail — Stricto
        </div>
        <div style="padding:32px 24px;color:#333;font-size:15px;line-height:1.8;">
          <p>Olá, <strong>{nome}</strong>! 👋</p>
          <p>Obrigado por se cadastrar no <strong>Stricto</strong>. Para ativar sua conta, confirme seu endereço de e-mail clicando no botão abaixo:</p>
          <div style="text-align:center;margin:32px 0;">
            <a href="{link}"
               style="background:#4F46E5;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;display:inline-block;">
              ✅ Verificar meu e-mail
            </a>
          </div>
          <p style="color:#666;font-size:13px;">
            Ou copie e cole este link no seu navegador:<br>
            <a href="{link}" style="color:#4F46E5;word-break:break-all;">{link}</a>
          </p>
          <p style="color:#999;font-size:12px;margin-top:24px;">
            ⚠️ Este link expira em <strong>24 horas</strong>. Se você não criou uma conta no Stricto, ignore este e-mail.
          </p>
        </div>
        <div style="padding:16px 24px;font-size:12px;color:#999;background:#f9f9f9;">
          © Stricto — Plataforma de Pós-Graduação
        </div>
      </div>
    </body>
    </html>
    """
 
 
# ─────────────────────────────────────────────
# ENVIAR EMAIL DE VERIFICAÇÃO
# ─────────────────────────────────────────────
 
async def enviar_email_verificacao(
    destinatario: str,
    nome: str,
    token_raw: str,
) -> bool:
    """
    Envia o email de verificação com o link contendo o token RAW.
    O token RAW nunca é salvo no banco — apenas o hash dele.
    """
    link = f"{BASE_URL}/auth/verificar-email?token={token_raw}"
 
    try:
        params = {
            "from": EMAIL_FROM,
            "to": [destinatario],
            "subject": "Confirme seu e-mail — Stricto",
            "html": _html_verificacao(nome, link),
            "text": f"Olá {nome}! Acesse o link para verificar seu e-mail: {link}\n\nO link expira em 24 horas.",
        }
        await run_in_threadpool(resend.Emails.send, params)
        return True
    except Exception as e:
        print(f"[RESEND ERROR - verificação] {e}")
        return False
 
 
# ─────────────────────────────────────────────
# ENVIAR EMAIL DE NOTIFICAÇÃO (já existia)
# ─────────────────────────────────────────────
 
async def enviar_email_notificacao(
    destinatario: str,
    titulo: str,
    mensagem: str,
) -> bool:
    try:
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
        print(f"[RESEND ERROR - notificação] {e}")
        return False
 