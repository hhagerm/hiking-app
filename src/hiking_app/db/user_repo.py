import asyncpg

from hiking_app.core.exceptions import EmailTaken, UsernameTaken
from hiking_app.models import User

ADD_USER_SQL = """
INSERT INTO users (
    email,
    username,
    password_hash
) VALUES ($1, $2, $3)
RETURNING id, username, email, create_ts
"""

class UserRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn
        
    async def add_user(
        self,
        email: str,  
        username: str, 
        password_hash: str,
        ):
        try:
            result = await self.conn.fetchrow(
                ADD_USER_SQL, 
                email, 
                username, 
                password_hash
                )
        except asyncpg.UniqueViolationError as e:
            if e.constraint_name == "users_email_lower_idx":
                raise EmailTaken() from e
            if e.constraint_name == "users_username_lower_idx":
                raise UsernameTaken() from e
            raise
        return User(
            id=result["id"],
            username=result["username"],
            email=result["email"],
            create_ts=result["create_ts"]
        )