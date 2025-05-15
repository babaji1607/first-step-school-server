from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from Utilities.token import decode_access_token
from sqlmodel import Session, select
from database import get_session
from models.users import User
from uuid import UUID

bearer_scheme = HTTPBearer()

ROLE_LEVEL = {
    "student": 1,
    "teacher": 2,
    "admin": 3,
}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    user = session.exec(select(User).where(User.id == UUID(user_id))).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_min_role(min_role: str):
    async def checker(user=Depends(get_current_user)):
        if ROLE_LEVEL.get(user.role, 0) < ROLE_LEVEL.get(min_role, 0):
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user
    return checker
