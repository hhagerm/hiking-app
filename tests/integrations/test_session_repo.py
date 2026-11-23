from datetime import datetime, timedelta, timezone

import pytest

from hiking_app.db import SessionRepository

TOKEN_HASH = b"fake-token-hash"

EXISTING_USER = {
    "email": "session@example.com",
    "username": "session_hiker",
    "password_hash": "fake-argon2-hash",
}


def expires_in(**delta) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**delta)


@pytest.fixture
async def user_id(conn):
    row = await conn.fetchrow(
        "INSERT INTO users (email, username, password_hash) "
        "VALUES ($1, $2, $3) RETURNING id",
        EXISTING_USER["email"],
        EXISTING_USER["username"],
        EXISTING_USER["password_hash"],
    )
    return row["id"]


async def test_add_session_stores_session_found_by_token(conn, user_id):
    repo = SessionRepository(conn)
    await repo.add_session(TOKEN_HASH, user_id, expires_in(hours=1))

    user = await repo.get_user_by_token(TOKEN_HASH)

    assert user is not None
    assert user.id == user_id
    assert user.username == EXISTING_USER["username"]
    assert user.email == EXISTING_USER["email"]


async def test_get_user_by_token_returns_none_on_unknown_token(conn, user_id):
    repo = SessionRepository(conn)
    await repo.add_session(TOKEN_HASH, user_id, expires_in(hours=1))

    user = await repo.get_user_by_token(b"some-other-token-hash")

    assert user is None


async def test_get_user_by_token_returns_none_on_expired_session(conn, user_id):
    repo = SessionRepository(conn)
    await repo.add_session(TOKEN_HASH, user_id, expires_in(hours=-1))

    user = await repo.get_user_by_token(TOKEN_HASH)

    assert user is None


async def test_get_user_by_token_returns_user_before_expiry(conn, user_id):
    repo = SessionRepository(conn)
    await repo.add_session(TOKEN_HASH, user_id, expires_in(seconds=30))

    user = await repo.get_user_by_token(TOKEN_HASH)

    assert user is not None
    assert user.id == user_id
