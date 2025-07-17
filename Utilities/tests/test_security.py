import pytest
from Utilities.security import hash_password, verify_password


def test_hash_password_returns_different_values_for_same_input():
    pw = "mysecretpassword"
    hashed1 = hash_password(pw)
    hashed2 = hash_password(pw)

    assert hashed1 != hashed2  # bcrypt adds salt, so hashes should differ
    assert hashed1.startswith("$2b$") or hashed1.startswith("$2a$") or hashed1.startswith("$2y$")


def test_verify_password_success():
    plain = "securepassword123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_failure():
    plain = "securepassword123"
    wrong = "wrongpassword456"
    hashed = hash_password(plain)
    assert verify_password(wrong, hashed) is False
