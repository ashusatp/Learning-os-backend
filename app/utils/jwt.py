from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import configs


def create_access_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=configs.ACCESS_TOKEN_EXPIRE_HOURS),
    }

    return jwt.encode(
        payload,
        configs.JWT_SECRET,
        algorithm=configs.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            configs.JWT_SECRET,
            algorithms=[configs.JWT_ALGORITHM],
        )
        return payload.get("sub")
    except JWTError:
        return None


def create_reset_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "purpose": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=configs.RESET_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, configs.JWT_SECRET, algorithm=configs.JWT_ALGORITHM)


def decode_reset_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            configs.JWT_SECRET,
            algorithms=[configs.JWT_ALGORITHM],
        )
        if payload.get("purpose") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None
