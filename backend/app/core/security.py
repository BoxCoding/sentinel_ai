"""JWT authentication + role-based access control.

Roles: admin, commander (city EOC), responder (police/fire/EMS),
hospital, citizen. Route dependencies enforce minimum role.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

ROLE_RANK = {"citizen": 0, "hospital": 1, "responder": 1, "commander": 2, "admin": 3}


class TokenUser(BaseModel):
    username: str
    role: str = "citizen"
    org: str | None = None


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode()[:72], hashed.encode())


def create_access_token(user: TokenUser) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user.username, "role": user.role, "org": user.org, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_error
        return TokenUser(username=username, role=payload.get("role", "citizen"), org=payload.get("org"))
    except JWTError:
        raise credentials_error


def require_role(minimum: str):
    async def checker(user: Annotated[TokenUser, Depends(get_current_user)]) -> TokenUser:
        if ROLE_RANK.get(user.role, -1) < ROLE_RANK[minimum]:
            raise HTTPException(status_code=403, detail=f"Requires role >= {minimum}")
        return user

    return checker
