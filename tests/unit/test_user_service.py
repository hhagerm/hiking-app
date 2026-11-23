from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock
from argon2 import PasswordHasher

from hiking_app.core.auth import hash_token
from hiking_app.service import UserService
from hiking_app.core.exceptions import ValidationFailed, EmailTaken, UsernameTaken, InvalidCredentials
from hiking_app.models import User

PASSWORD = "Str0ng!pass"
PASSWORD_HASH = PasswordHasher().hash(PASSWORD)
USERNAME = "hiker"

USER = User(
    id=7,
    username=USERNAME,
    email="mail@example.com",
    create_ts=datetime(2026, 1, 1, tzinfo=timezone.utc),
)


def valid_registration() -> dict:
    return {
        "email": "MAIL@example.com",
        "username": USERNAME,
        "password1": PASSWORD,
        "password2": PASSWORD,
    }

async def test_register_account_stores_hashed_password():
    user_repo = AsyncMock()
    service = UserService(user_repo, AsyncMock())

    await service.register_account(
        **valid_registration()
    )

    email, username, stored_hash = user_repo.add_user.await_args.args
    assert email == "mail@example.com"
    assert PasswordHasher().verify(stored_hash, "Str0ng!pass")
    
@pytest.mark.parametrize(
    "password, expected_message",
    [
        pytest.param("Sh0rt!a", "must be between 8 and 64 characters", id="too_short"),
        pytest.param("L0ng!"*13, "must be between 8 and 64 characters", id="too_long"),
        pytest.param("str0ng!pass", "must contain an uppercase letter", id="no_upper"),
        pytest.param("STR0NG!PASS", "must contain a lowercase letter", id="no_lower"),
        pytest.param("Strong!pass", "must contain a digit", id="no_digit"),
        pytest.param("Str0ngpass", "must contain a special character", id="no_special"),
    ],
)
async def test_register_rejects_weak_password(password, expected_message):
    user_repo = AsyncMock()
    service = UserService(user_repo, AsyncMock())
    payload = valid_registration() | {"password1": password, "password2": password}
    
    with pytest.raises(ValidationFailed) as exc_info:
        await service.register_account(**payload)
        
    assert exc_info.value.field == "password1"
    assert exc_info.value.message == expected_message
    user_repo.add_user.assert_not_awaited()
    
async def test_register_rejects_mismatched_passwords():
    user_repo = AsyncMock()
    service = UserService(user_repo, AsyncMock())
    
    payload = valid_registration() | {"password2": "M1sM@atchedPswd"}
    
    with pytest.raises(ValidationFailed) as exc_info:
        await service.register_account(**payload)
    
    assert exc_info.value.field == "password2"
    assert exc_info.value.message == "passwords do not match"
    user_repo.add_user.assert_not_awaited()
    
@pytest.mark.parametrize(
    "username, expected_message",
    [
        pytest.param("sh", "must be between 3 and 32 characters", id="too_short"),
        pytest.param("lng"*11, "must be between 3 and 32 characters", id="too_long"),
    ],
)
async def test_register_rejects_short_or_long_username(username, expected_message):
    user_repo = AsyncMock()
    service = UserService(user_repo, AsyncMock())
    payload = valid_registration() | {"username": username}
    
    with pytest.raises(ValidationFailed) as exc_info:
        await service.register_account(**payload)
        
    assert exc_info.value.field == "username"
    assert exc_info.value.message == expected_message
    user_repo.add_user.assert_not_awaited()
    

async def test_register_rejects_invalid_email():
    user_repo = AsyncMock()
    service = UserService(user_repo, AsyncMock())
    payload = valid_registration() | {"email": "not-an-email"}

    with pytest.raises(ValidationFailed) as exc_info:
        await service.register_account(**payload)

    assert exc_info.value.field == "email"
    user_repo.add_user.assert_not_awaited()

@pytest.mark.parametrize(
    "exception, field, message",
    [
        pytest.param(EmailTaken, "email", "email already taken", id="email_taken"),
        pytest.param(UsernameTaken, "username", "username already taken", id="username_taken"),
    ],
)
async def test_register_rejects_taken_username_or_email(exception, field, message):
    user_repo = AsyncMock()
    user_repo.add_user.side_effect = exception()
    service = UserService(user_repo, AsyncMock())

    with pytest.raises(ValidationFailed) as exc_info:
        await service.register_account(**valid_registration())

    assert exc_info.value.field == field
    assert exc_info.value.message == message
    user_repo.add_user.assert_awaited()
    
async def test_login_returns_user_and_stores_hashed_token():
    user_repo = AsyncMock()
    user_repo.get_user.return_value = USER
    user_repo.get_password_hash.return_value = PASSWORD_HASH
    session_repo = AsyncMock()
    service = UserService(user_repo, session_repo)

    user, raw = await service.login_user("hiker", PASSWORD)

    assert user is USER

    token_hash, user_id, expires_ts = session_repo.add_session.await_args.args
    assert token_hash == hash_token(raw)
    assert user_id == 7
    assert expires_ts > datetime.now(timezone.utc)
    
async def test_login_rejects_invalid_credentials():
    user_repo = AsyncMock()
    user_repo.get_user.return_value = None
    user_repo.get_password_hash.return_value = PASSWORD_HASH
    session_repo = AsyncMock()
    service = UserService(user_repo, session_repo)
    
    with pytest.raises(InvalidCredentials):
        await service.login_user("ghost", PASSWORD)

    user_repo.get_password_hash.assert_not_awaited()
    session_repo.add_session.assert_not_awaited()
    

async def test_login_rejects_invalid_password():
    user_repo = AsyncMock()
    user_repo.get_user.return_value = USER
    user_repo.get_password_hash.return_value = PASSWORD_HASH
    session_repo = AsyncMock()
    service = UserService(user_repo, session_repo)

    with pytest.raises(InvalidCredentials):
        await service.login_user("hiker", "1nVal!dPassword")

    user_repo.get_password_hash.assert_awaited_once()
    session_repo.add_session.assert_not_awaited()