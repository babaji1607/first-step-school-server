import pytest
from datetime import timedelta, datetime
from jose import jwt

from Utilities.token import create_access_token, decode_access_token

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def test_create_access_token_returns_valid_jwt():
    data = {"sub": "test-user-id"}
    token = create_access_token(data)

    assert isinstance(token, str)

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "test-user-id"
    assert "exp" in decoded


def test_create_access_token_with_expiration():
    data = {"sub": "another-user"}
    expire_in = timedelta(minutes=5)
    token = create_access_token(data, expires_delta=expire_in)

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = datetime.utcfromtimestamp(decoded["exp"])
    now = datetime.utcnow()
    delta_seconds = (exp - now).total_seconds()

    # Accept some clock drift (~10 seconds)
    assert 290 <= delta_seconds <= 310, f"Expiration delta was {delta_seconds} seconds"
    assert decoded["sub"] == "another-user"

def test_decode_access_token_valid_token():
    payload = {
        "sub": "valid-user",
        "exp": datetime.utcnow() + timedelta(minutes=5)  # ✅ use datetime object directly
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "valid-user"


def test_decode_access_token_invalid_token_returns_none():
    invalid_token = "this.is.not.valid.jwt"
    result = decode_access_token(invalid_token)
    assert result is None


def test_decode_access_token_with_wrong_secret_returns_none():
    data = {"sub": "hacker", "exp": datetime.utcnow().timestamp() + 300}
    token = jwt.encode(data, "wrong-secret", algorithm=ALGORITHM)

    result = decode_access_token(token)
    assert result is None
