from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class WorkScopeType(str, Enum):
    kitchen = "kitchen"
    bathroom = "bathroom"
    partial = "partial"
    full_remodeling = "full_remodeling"


class UnitTypeChip(BaseModel):
    unit_type_id: int
    exclusive_area_m2: Decimal
    type_code: str | None = None
    room_count: int | None = None
    bathroom_count: int | None = None
    structure_keyword: str | None = None
    portfolio_count: int


class ComplexDetailResponse(BaseModel):
    complex_id: int
    name: str
    address: str
    built_year: int | None = None
    household_count: int | None = None
    unit_types: list[UnitTypeChip]


class PortfolioCard(BaseModel):
    portfolio_id: int
    title: str
    before_image_url: str | None = None
    after_image_url: str | None = None
    work_scope: WorkScopeType
    style: str
    budget_min_krw: int | None = None
    budget_max_krw: int | None = None
    duration_days: int | None = None
    vendor_id: int | None = None
    vendor_name: str | None = None


class PortfolioFilterQuery(BaseModel):
    min_area: float | None = Field(default=None, ge=0)
    max_area: float | None = Field(default=None, ge=0)
    budget_min_krw: int | None = Field(default=None, ge=0)
    budget_max_krw: int | None = Field(default=None, ge=0)
    work_scope: WorkScopeType | None = None
    style: str | None = None
    limit: int = Field(default=30, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.min_area is not None and self.max_area is not None and self.min_area > self.max_area:
            raise ValueError("min_area must be <= max_area")
        if (
            self.budget_min_krw is not None
            and self.budget_max_krw is not None
            and self.budget_min_krw > self.budget_max_krw
        ):
            raise ValueError("budget_min_krw must be <= budget_max_krw")
        return self


class PortfolioListResponse(BaseModel):
    items: list[PortfolioCard]
    total: int


class FavoriteCreateRequest(BaseModel):
    user_key: str = Field(..., min_length=1, max_length=80)
    portfolio_id: int


class FavoriteResponse(BaseModel):
    favorite_id: int
    user_key: str
    portfolio_id: int
