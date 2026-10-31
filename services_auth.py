from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import DUMMY_HASH, hash_password, verify_password
from models import User


class EmailAlreadyRegisteredError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == normalize_email(email)).first()


def register_user(db: Session, email: str, password: str) -> User:
    email = normalize_email(email)

    if get_user_by_email(db, email):
        raise EmailAlreadyRegisteredError(email)

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)

    try:
        db.commit()
    except IntegrityError:  # two requests registered the same email at once
        db.rollback()
        raise EmailAlreadyRegisteredError(email)

    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)

    if user is None or not user.password_hash:
        verify_password(password, DUMMY_HASH)  # same timing either way
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user