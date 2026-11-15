import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import redis
from fastapi import Depends, HTTPException, Request, WebSocket, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database import get_db
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REDIS_URL, SECRET_KEY
from models import User

ALGORITHM = "HS256"
COOKIE_NAME = "access_token"

logger = logging.getLogger(__name__)

# Redis remembers which tokens were logged out (until they would have expired anyway)
_redis_client: redis.Redis | None = None


class TokenRevocationUnavailableError(Exception):
    """Redis could not be reached to read or write token revocation state."""


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
        raise TokenRevocationUnavailableError from None
    return True


def is_token_revoked(jti: str) -> bool:
    try:
        return bool(_redis().exists(_revoked_key(jti)))
    except redis.RedisError:
        logger.exception("Could not check token revocation: Redis is unavailable")
        raise TokenRevocationUnavailableError from None


def check_redis() -> None:
    """Raise when Redis cannot serve token-revocation operations."""
    try:
        _redis().ping()
    except redis.RedisError:
        logger.exception("Could not reach Redis: Redis is unavailable")
        raise TokenRevocationUnavailableError from None


def _authenticate_token(token: str | None, db: Session) -> User:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not logged in or session expired",
    )

    if not token:
        raise error

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp", "iat", "jti"]},
        )
        subject = payload["sub"]
        if not isinstance(subject, str):
            raise ValueError("Token subject must be a string")
        user_id = uuid.UUID(subject)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error

    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        raise error

    try:
        revoked = is_token_revoked(jti)
    except TokenRevocationUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session service is temporarily unavailable",
        ) from exc
    if revoked:
        raise error

    user = db.get(User, user_id)
    if user is None:
        raise error
    password_changed_at = user.password_changed_at
    token_issued_at = payload["iat"]
    if password_changed_at is not None:
        changed_at = password_changed_at.replace(tzinfo=timezone.utc).timestamp()
        if token_issued_at < changed_at:
            raise error
    return user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    return _authenticate_token(request.cookies.get(COOKIE_NAME), db)


def get_current_websocket_user(
    websocket: WebSocket,
    db: Session,
) -> User:
    return _authenticate_token(websocket.cookies.get(COOKIE_NAME), db)