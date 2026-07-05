"""Auth routes. Demo users are seeded in-memory; production reads the users
table in AlloyDB with hashes from Secret Manager-managed salt."""
from fastapi import APIRouter, HTTPException

from app.core.security import TokenUser, create_access_token, hash_password, verify_password
from app.schemas.api import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_USERS = {
    "admin": {"password": hash_password("admin123"), "role": "admin", "org": "City EOC"},
    "commander": {"password": hash_password("command123"), "role": "commander", "org": "City EOC"},
    "responder": {"password": hash_password("respond123"), "role": "responder", "org": "Fire Dept"},
    "hospital": {"password": hash_password("hospital123"), "role": "hospital", "org": "City General"},
    "citizen": {"password": hash_password("citizen123"), "role": "citizen", "org": None},
}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = DEMO_USERS.get(body.username)
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(TokenUser(username=body.username,
                                          role=user["role"], org=user["org"]))
    return TokenResponse(access_token=token, role=user["role"])
