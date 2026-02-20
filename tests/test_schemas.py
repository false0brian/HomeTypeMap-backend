import pytest
from pydantic import ValidationError

from app.schemas.portfolio import PortfolioFilterQuery, WorkScopeType


def test_portfolio_filter_query_invalid_area_range() -> None:
    with pytest.raises(ValidationError):
        PortfolioFilterQuery(min_area=84, max_area=59)


def test_portfolio_filter_query_invalid_budget_range() -> None:
    with pytest.raises(ValidationError):
        PortfolioFilterQuery(budget_min_krw=50000000, budget_max_krw=30000000)


def test_portfolio_filter_query_valid_enum() -> None:
    query = PortfolioFilterQuery(work_scope=WorkScopeType.full_remodeling, limit=10, offset=0)
    assert query.work_scope == WorkScopeType.full_remodeling
