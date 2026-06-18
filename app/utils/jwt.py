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
