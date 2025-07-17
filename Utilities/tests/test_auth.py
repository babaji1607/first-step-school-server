import pytest
from uuid import uuid4
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session
from unittest.mock import patch, MagicMock

from Utilities.auth import get_current_user, require_min_role
from models.users import User


@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        role="admin",
        name="Test User",
        email="admin@example.com"
    )


@pytest.fixture
def mock_credentials():
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="mocktoken"
    )


@pytest.fixture
def mock_session(mock_user):
    # Fake a SQLModel session where .exec().first() returns mock_user
    session = MagicMock(spec=Session)
    session.exec.return_value.first.return_value = mock_user
    return session


@patch("Utilities.auth.decode_access_token")
@pytest.mark.asyncio
async def test_get_current_user_valid_token(mock_decode, mock_credentials, mock_session, mock_user):
    mock_decode.return_value = {"sub": str(mock_user.id)}

    user = await get_current_user(mock_credentials, mock_session)
    assert user == mock_user


@patch("Utilities.auth.decode_access_token")
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_decode, mock_credentials, mock_session):
    mock_decode.return_value = None

    with pytest.raises(HTTPException) as exc:
        await get_current_user(mock_credentials, mock_session)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token"


@patch("Utilities.auth.decode_access_token")
@pytest.mark.asyncio
async def test_get_current_user_user_not_found(mock_decode, mock_credentials):
    mock_decode.return_value = {"sub": str(uuid4())}
    session = MagicMock(spec=Session)
    session.exec.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        await get_current_user(mock_credentials, session)
    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found"


@pytest.mark.asyncio
async def test_require_min_role_allows_admin(mock_user):
    mock_user.role = "admin"
    checker = require_min_role("teacher")  # teacher requires lower privilege than admin
    result = await checker(user=mock_user)
    assert result == mock_user


@pytest.mark.asyncio
async def test_require_min_role_blocks_student(mock_user):
    mock_user.role = "student"
    checker = require_min_role("admin")  # student shouldn't access admin routes

    with pytest.raises(HTTPException) as exc:
        await checker(user=mock_user)
    assert exc.value.status_code == 403
    assert exc.value.detail == "Insufficient privileges"


