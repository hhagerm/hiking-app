from datetime import datetime, timedelta, timezone
import hashlib
import secrets

SESSION_TTL = timedelta(days=30)

def new_session_token() -> tuple[str, bytes, datetime]:
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).digest()
    expires_ts = datetime.now(timezone.utc) + SESSION_TTL
    return raw, token_hash, expires_ts