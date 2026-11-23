import pytest

from hiking_app.core.exceptions import EmailTaken, UsernameTaken
from hiking_app.db import UserRepository

EXISTING_USER = {
    "email": "existing@example.com",
    "username": "existing_hiker",
    "password_hash": "fake-argon2-hash",
}


@pytest.fixture
async def existing_user(conn):
    await conn.execute(
        "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
        EXISTING_USER["email"],
        EXISTING_USER["username"],
        EXISTING_USER["password_hash"],
    )


class TestAddUser:
    async def test_add_user_returns_created_user(self, conn):
        user = await UserRepository(conn).add_user(
            email="new@example.com",
            username="new_hiker",
            password_hash="fake-argon2-hash",
        )

        assert user.email == "new@example.com"
        assert user.username == "new_hiker"
        assert user.id is not None
        assert user.create_ts is not None

    async def test_add_user_raises_email_taken_on_duplicate_email(
        self, conn, existing_user
    ):
        with pytest.raises(EmailTaken):
            await UserRepository(conn).add_user(
                email=EXISTING_USER["email"],
                username="different_hiker",
                password_hash="fake-argon2-hash",
            )

    async def test_add_user_raises_email_taken_on_differently_cased_email(
        self, conn, existing_user
    ):
        with pytest.raises(EmailTaken):
            await UserRepository(conn).add_user(
                email=EXISTING_USER["email"].upper(),
                username="different_hiker",
                password_hash="fake-argon2-hash",
            )

    async def test_add_user_raises_username_taken_on_duplicate_username(
        self, conn, existing_user
    ):
        with pytest.raises(UsernameTaken):
            await UserRepository(conn).add_user(
                email="different@example.com",
                username=EXISTING_USER["username"],
                password_hash="fake-argon2-hash",
            )


class TestGetUser:
    async def test_get_user_returns_user_on_match(self, conn, existing_user):
        user = await UserRepository(conn).get_user(EXISTING_USER["username"])

        assert user is not None
        assert user.username == EXISTING_USER["username"]
        assert user.email == EXISTING_USER["email"]

    async def test_get_user_matches_username_case_insensitively(
        self, conn, existing_user
    ):
        user = await UserRepository(conn).get_user(
            EXISTING_USER["username"].upper()
        )

        assert user is not None
        assert user.username == EXISTING_USER["username"]

    async def test_get_user_returns_none_when_user_missing(self, conn):
        user = await UserRepository(conn).get_user("ghost_hiker")

        assert user is None


class TestGetPasswordHash:
    async def test_get_password_hash_returns_hash_on_match(self, conn, existing_user):
        password_hash = await UserRepository(conn).get_password_hash(
            EXISTING_USER["username"]
        )

        assert password_hash == EXISTING_USER["password_hash"]

    async def test_get_password_hash_matches_username_case_insensitively(
        self, conn, existing_user
    ):
        password_hash = await UserRepository(conn).get_password_hash(
            EXISTING_USER["username"].upper()
        )

        assert password_hash == EXISTING_USER["password_hash"]

    async def test_get_password_hash_returns_none_when_user_missing(self, conn):
        password_hash = await UserRepository(conn).get_password_hash("ghost_hiker")

        assert password_hash is None
