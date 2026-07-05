from app.core.security import (TokenUser, create_access_token, hash_password,
                               verify_password)
from jose import jwt

from app.core.config import settings


def test_password_roundtrip():
    hashed = hash_password("s3cret!")
    assert verify_password("s3cret!", hashed)
    assert not verify_password("wrong", hashed)


def test_token_carries_role():
    token = create_access_token(TokenUser(username="cmd", role="commander", org="EOC"))
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "cmd"
    assert payload["role"] == "commander"
