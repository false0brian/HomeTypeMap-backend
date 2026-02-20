from datetime import date

from pydantic import BaseModel, Field


class QuoteRequestCreate(BaseModel):
    user_key: str = Field(..., min_length=1, max_length=80)
    vendor_id: int | None = None
    portfolio_id: int | None = None
    preferred_date: date | None = None
    message: str | None = Field(default=None, max_length=2000)


class QuoteRequestResponse(BaseModel):
    quote_request_id: int
    user_key: str
    vendor_id: int | None = None
    portfolio_id: int | None = None
