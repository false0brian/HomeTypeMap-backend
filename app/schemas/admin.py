from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class PublishStatus(str, Enum):
    draft = "draft"
    review = "review"
    published = "published"


class AdminPortfolioBase(BaseModel):
    complex_id: int
    unit_type_id: int
    vendor_id: int | None = None
    title: str = Field(..., min_length=1, max_length=220)
    before_image_url: str | None = Field(default=None, max_length=500)
    after_image_url: str | None = Field(default=None, max_length=500)
    work_scope: str = Field(..., min_length=1, max_length=80)
    style: str = Field(..., min_length=1, max_length=80)
    budget_min_krw: int | None = Field(default=None, ge=0)
    budget_max_krw: int | None = Field(default=None, ge=0)
    duration_days: int | None = Field(default=None, ge=0)
    tags: str | None = None
    summary: str | None = None
    status: PublishStatus = PublishStatus.draft

    @model_validator(mode="after")
    def validate_budget_order(self):
        if (
            self.budget_min_krw is not None
            and self.budget_max_krw is not None
            and self.budget_min_krw > self.budget_max_krw
        ):
            raise ValueError("budget_min_krw must be <= budget_max_krw")
        return self


class AdminPortfolioCreate(AdminPortfolioBase):
    pass


class AdminPortfolioUpdate(BaseModel):
    complex_id: int | None = None
    unit_type_id: int | None = None
    vendor_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=220)
    before_image_url: str | None = Field(default=None, max_length=500)
    after_image_url: str | None = Field(default=None, max_length=500)
    work_scope: str | None = Field(default=None, min_length=1, max_length=80)
    style: str | None = Field(default=None, min_length=1, max_length=80)
    budget_min_krw: int | None = Field(default=None, ge=0)
    budget_max_krw: int | None = Field(default=None, ge=0)
    duration_days: int | None = Field(default=None, ge=0)
    tags: str | None = None
    summary: str | None = None
    status: PublishStatus | None = None

    @model_validator(mode="after")
    def validate_budget_order(self):
        if (
            self.budget_min_krw is not None
            and self.budget_max_krw is not None
            and self.budget_min_krw > self.budget_max_krw
        ):
            raise ValueError("budget_min_krw must be <= budget_max_krw")
        return self


class AdminPortfolioResponse(BaseModel):
    portfolio_id: int
    complex_id: int
    unit_type_id: int
    vendor_id: int | None = None
    title: str
    work_scope: str
    style: str
    status: PublishStatus
    budget_min_krw: int | None = None
    budget_max_krw: int | None = None
    duration_days: int | None = None
    published_at: datetime | None = None
    created_at: datetime


class AdminBlogPostBase(BaseModel):
    vendor_id: int | None = None
    title: str = Field(..., min_length=1, max_length=220)
    slug: str = Field(..., min_length=1, max_length=140)
    excerpt: str | None = Field(default=None, max_length=500)
    content: str = Field(..., min_length=1)
    status: PublishStatus = PublishStatus.draft


class AdminBlogPostCreate(AdminBlogPostBase):
    pass


class AdminBlogPostUpdate(BaseModel):
    vendor_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=220)
    slug: str | None = Field(default=None, min_length=1, max_length=140)
    excerpt: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, min_length=1)
    status: PublishStatus | None = None


class AdminBlogPostResponse(BaseModel):
    post_id: int
    vendor_id: int | None = None
    title: str
    slug: str
    excerpt: str | None = None
    content: str
    status: PublishStatus
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
