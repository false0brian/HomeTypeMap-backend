from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import QuoteRequest


def create_quote_request(
    db: Session,
    user_key: str,
    vendor_id: int | None,
    portfolio_id: int | None,
    preferred_date,
    message: str | None,
) -> QuoteRequest:
    if vendor_id is None and portfolio_id is None:
        raise HTTPException(status_code=422, detail="vendor_id or portfolio_id is required")

    req = QuoteRequest(
        user_key=user_key,
        vendor_id=vendor_id,
        portfolio_id=portfolio_id,
        preferred_date=preferred_date,
        message=message,
    )
    db.add(req)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="invalid vendor_id or portfolio_id") from exc
    db.refresh(req)
    return req
