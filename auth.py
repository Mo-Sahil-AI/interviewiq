import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import redis
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database import get_db
from models import User

load_dotenv()

_secret_key = os.getenv("SECRET_KEY")
if not _secret_key:
    raise ValueError("SECRET_KEY not found in .env")

SECRET_KEY: str = _secret_key

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "2880"))
COOKIE_NAME = "access_token"

logger = logging.getLogger(__name__)

# Redis remembers which tokens were logged out (until they would have expired anyway)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _redis_client


def _revoked_key(jti: str) -> str:
    return f"revoked_token:{jti}"

password_hasher = PasswordHash.recommended()  # Argon2id

# Used to keep login timing the same when the email doesn't exist
DUMMY_HASH = password_hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": uuid.uuid4().hex,   # unique id, so one token can be revoked on logout
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def revoke_token(token: str) -> bool:
    """Make a token stop working right now (used by /logout)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return False   # already expired or invalid: nothing to revoke

    jti, exp = payload.get("jti"), payload.get("exp")
    if not jti or not exp:
        return False   # token from before this change

    seconds_left = int(exp - time.time())
    if seconds_left <= 0:
        return False

    try:
        _redis().set(_revoked_key(jti), "1", ex=seconds_left)
    except redis.RedisError:
        logger.exception("Could not revoke the token: Redis is unavailable")
        return False
    return True


def is_token_revoked(jti: str) -> bool:
    try:
        return bool(_redis().exists(_revoked_key(jti)))
    except redis.RedisError:
        # If Redis is down we let the request through rather than lock everyone out.
        logger.exception("Could not check token revocation: Redis is unavailable")
        return False


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not logged in or session expired",
    )

    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise error

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload.get("sub", ""))
    except (jwt.InvalidTokenError, ValueError):
        raise error

    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise error

    user = db.get(User, user_id)
    if user is None:
        raise error
    return user