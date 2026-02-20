import sqlite3
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.services.favorite_service import create_favorite
from app.services.quote_service import create_quote_request


class DummyDB:
    def __init__(self, should_fail_commit: bool = False):
        self.should_fail_commit = should_fail_commit
        self.added = []
        self.rolled_back = False

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        if self.should_fail_commit:
            raise IntegrityError("insert", {}, sqlite3.IntegrityError("constraint"))

    def rollback(self):
        self.rolled_back = True

    def refresh(self, obj):
        obj.id = 1


def test_create_quote_request_requires_vendor_or_portfolio() -> None:
    db = DummyDB()
    with pytest.raises(HTTPException) as exc_info:
        create_quote_request(
            db=db,
            user_key="user-1",
            vendor_id=None,
            portfolio_id=None,
            preferred_date=None,
            message="문의",
        )
    assert exc_info.value.status_code == 422


def test_create_quote_request_integrity_error_maps_to_400() -> None:
    db = DummyDB(should_fail_commit=True)
    with pytest.raises(HTTPException) as exc_info:
        create_quote_request(
            db=db,
            user_key="user-1",
            vendor_id=10,
            portfolio_id=None,
            preferred_date=date(2026, 2, 20),
            message="문의",
        )
    assert exc_info.value.status_code == 400
    assert db.rolled_back is True


def test_create_favorite_integrity_error_maps_to_409() -> None:
    db = DummyDB(should_fail_commit=True)
    with pytest.raises(HTTPException) as exc_info:
        create_favorite(db=db, user_key="user-1", portfolio_id=9001)
    assert exc_info.value.status_code == 409
    assert db.rolled_back is True


def test_create_favorite_success() -> None:
    db = DummyDB(should_fail_commit=False)
    favorite = create_favorite(db=db, user_key="user-1", portfolio_id=9001)
    assert favorite.id == 1
    assert favorite.user_key == "user-1"
    assert favorite.portfolio_id == 9001
