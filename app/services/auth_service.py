from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import unicodedata
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AppUser, AuthSession

_PASSWORD_ALGO = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 260000
_SESSION_TTL_DAYS = 30


def _normalize_email(email: str) -> str:
    normalized = unicodedata.normalize("NFKC", email).strip().lower()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise HTTPException(status_code=422, detail="invalid email")
    return normalized


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    dk_b64 = base64.b64encode(dk).decode("ascii")
    return f"{_PASSWORD_ALGO}${_PASSWORD_ITERATIONS}${salt_b64}${dk_b64}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iter_str, salt_b64, expected_b64 = encoded.split("$", 3)
    except ValueError:
        return False
    if algo != _PASSWORD_ALGO:
        return False
    try:
        iterations = int(iter_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(expected_b64.encode("ascii"))
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def _next_user_key(db: Session, display_name: str) -> str:
    base = "".join(ch for ch in display_name.lower() if ch.isalnum())[:24] or "user"
    for _ in range(30):
        suffix = secrets.token_hex(3)
        candidate = f"{base}-{suffix}"
        exists = db.execute(select(AppUser.id).where(AppUser.user_key == candidate)).scalar_one_or_none()
        if exists is None:
            return candidate
    return f"user-{secrets.token_hex(6)}"


def _new_session(db: Session, user: AppUser) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=_SESSION_TTL_DAYS)
    session = AuthSession(user_id=user.id, token_hash=_token_hash(token), expires_at=expires_at)
    db.add(session)
    db.commit()
    return token, expires_at


def signup(db: Session, email: str, password: str, display_name: str) -> tuple[str, datetime, AppUser]:
    normalized_email = _normalize_email(email)
    existing = db.execute(select(AppUser).where(AppUser.email == normalized_email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="email already exists")

    user = AppUser(
        email=normalized_email,
        display_name=display_name.strip(),
        user_key=_next_user_key(db, display_name),
        password_hash=_hash_password(password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="failed to create user") from exc
    db.refresh(user)
    token, expires_at = _new_session(db, user)
    return token, expires_at, user


def login(db: Session, email: str, password: str) -> tuple[str, datetime, AppUser]:
    normalized_email = _normalize_email(email)
    user = db.execute(select(AppUser).where(AppUser.email == normalized_email)).scalar_one_or_none()
    if user is None or not _verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid email or password")
    token, expires_at = _new_session(db, user)
    return token, expires_at, user


def get_user_by_token(db: Session, token: str) -> AppUser | None:
    if not token:
        return None
    now = datetime.now(UTC)
    row = db.execute(
      select(AuthSession, AppUser)
      .join(AppUser, AppUser.id == AuthSession.user_id)
      .where(AuthSession.token_hash == _token_hash(token))
      .where(AuthSession.expires_at > now)
    ).first()
    if row is None:
        return None
    return row[1]


def logout(db: Session, token: str) -> None:
    if not token:
        return
    db.execute(delete(AuthSession).where(AuthSession.token_hash == _token_hash(token)))
    db.commit()
