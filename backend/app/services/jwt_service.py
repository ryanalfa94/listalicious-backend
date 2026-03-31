
# app/services/jwt_service.py
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import uuid


SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_ME_DEV_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))  # e.g., 15–60 in prod

def create_access_token(*, subject: str, token_version: int, extra: dict | None = None, expires_delta: timedelta | None = None) -> str:
    """
    subject: user_id (string)
    token_version: the current user's token_version from DB
    extra: optional extra claims (e.g., email)
    """
    now = datetime.now(timezone.utc)
    exp = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": subject,             # user_id
        "tv": int(token_version),   # token_version
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Reject tokens that are not access tokens (e.g. a future refresh token
        # should never be accepted where an access token is expected).
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None
