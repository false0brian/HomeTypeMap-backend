from datetime import date
from datetime import datetime

from pydantic import BaseModel, Field


class QuoteRequestCreate(BaseModel):
    user_key: str | None = Field(default=None, min_length=1, max_length=80)
    requester_name: str | None = Field(default=None, min_length=1, max_length=80)
    requester_email: str | None = Field(default=None, min_length=3, max_length=160)
    vendor_id: int | None = None
    portfolio_id: int | None = None
    preferred_date: date | None = None
    message: str | None = Field(default=None, max_length=2000)


class QuoteRequestResponse(BaseModel):
    quote_request_id: int
    user_key: str
    requester_name: str | None = None
    requester_email: str | None = None
    vendor_id: int | None = None
    portfolio_id: int | None = None
    created_at: datetime
