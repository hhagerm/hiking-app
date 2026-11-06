from datetime import datetime

import asyncpg

ADD_SESSION_SQL = """
INSERT INTO sessions (
    token_hash,
    user_id,
    expires_ts
) VALUES ($1, $2, $3)
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