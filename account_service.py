import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from models import User

TOKEN_TTL = timedelta(hours=1)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_token() -> str:
    return secrets.token_urlsafe(32)


def issue_email_verification(db: Session, user: User) -> str:
    token = _new_token()
    user.email_verification_token_hash = _hash_token(token)
    user.email_verification_expires_at = _utc_now() + TOKEN_TTL
    db.commit()
    return token


def consume_email_verification(db: Session, token: str) -> User | None:
    user = db.query(User).filter(
        User.email_verification_token_hash == _hash_token(token),
        User.email_verification_expires_at > _utc_now(),
    ).first()
    if user is None:
        return None
    user.email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.commit()
    return user


def issue_password_reset(db: Session, user: User) -> str:
    token = _new_token()
    user.password_reset_token_hash = _hash_token(token)
    user.password_reset_expires_at = _utc_now() + TOKEN_TTL
    db.commit()
    return token


def consume_password_reset(db: Session, token: str) -> User | None:
    user = db.query(User).filter(
        User.password_reset_token_hash == _hash_token(token),
        User.password_reset_expires_at > _utc_now(),
    ).first()
    if user is None:
        return None
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.commit()
    return user
