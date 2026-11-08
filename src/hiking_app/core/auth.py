from datetime import datetime, timedelta, timezone
import hashlib
import secrets

SESSION_TTL = timedelta(days=30)

def hash_token(raw: str) -> bytes:
    return hashlib.sha256(raw.encode()).digest()

def new_session_token() -> tuple[str, bytes, datetime]:
    raw = secrets.token_urlsafe(32)
    expires_ts = datetime.now(timezone.utc) + SESSION_TTL
    return raw, hash_token(raw), expires_ts