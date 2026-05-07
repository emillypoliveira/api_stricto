import secrets
import hashlib
from datetime import datetime, timedelta

def gerar_token_verificacao() -> tuple[str, str, datetime]:
    """Retorna (token_raw, token_hash, expira_em)"""
    token_raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
    expira_em = datetime.utcnow() + timedelta(hours=24)
    return token_raw, token_hash, expira_em