from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import UserFavorite


def create_favorite(db: Session, user_key: str, portfolio_id: int) -> UserFavorite:
    favorite = UserFavorite(user_key=user_key, portfolio_id=portfolio_id)
    db.add(favorite)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="favorite already exists or portfolio does not exist") from exc
    db.refresh(favorite)
    return favorite


def list_favorites(db: Session, user_key: str) -> list[UserFavorite]:
    rows = db.execute(
        select(UserFavorite)
        .where(UserFavorite.user_key == user_key)
        .order_by(UserFavorite.created_at.desc())
    ).scalars()
    return list(rows)
