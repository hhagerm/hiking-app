from datetime import datetime

import asyncpg

from hiking_app.models import User

ADD_SESSION_SQL = """
INSERT INTO sessions (
    token_hash,
    user_id,
    expires_ts
) VALUES ($1, $2, $3)
"""

GET_SESSION_USER_SQL = """
SELECT u.id, u.username, u.email, u.create_ts
FROM sessions s
JOIN users u ON u.id = s.user_id
WHERE s.token_hash = $1
  AND s.expires_ts > now()
"""

class SessionRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn
        
    async def add_session(
        self,
        token_hash: bytes,
        user_id: int,
        expires_ts: datetime,
    ):
        await self.conn.execute(ADD_SESSION_SQL, token_hash, user_id, expires_ts)
    
    async def get_user_by_token(self, token_hash: bytes) -> User | None:
        result = await self.conn.fetchrow(GET_SESSION_USER_SQL, token_hash)
        if result is None:
            return None
        return User(
            id=result["id"],
            username=result["username"],
            email=result["email"],
            create_ts=result["create_ts"],
        )