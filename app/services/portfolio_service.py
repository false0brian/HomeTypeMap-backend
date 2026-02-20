from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Complex, FloorPlan, Portfolio, UnitType, Vendor
from app.schemas.portfolio import (
    ComplexDetailResponse,
    PortfolioCard,
    PortfolioFilterQuery,
    PortfolioListResponse,
    UnitTypeChip,
)


def _compute_floor_plan_pins(portfolio_id: int) -> tuple[float, float, float, float]:
    # Floor plan pin positions are normalized percentages so front can render
    # pin-to-image matching even when source coordinates are missing.
    base_x = 18 + (portfolio_id * 17 % 64)
    base_y = 16 + (portfolio_id * 13 % 66)
    before_x = float(base_x)
    before_y = float(base_y)
    after_x = min(92.0, before_x + 6.0)
    after_y = min(92.0, before_y + 4.0)
    return before_x, before_y, after_x, after_y


def get_complex_detail(db: Session, complex_id: int) -> ComplexDetailResponse | None:
    complex_row = db.get(Complex, complex_id)
    if complex_row is None:
        return None

    type_rows = db.execute(
        select(
            UnitType.id,
            UnitType.exclusive_area_m2,
            UnitType.type_code,
            UnitType.room_count,
            UnitType.bathroom_count,
            UnitType.structure_keyword,
            func.min(FloorPlan.image_url).label("floor_plan_image_url"),
            func.count(Portfolio.id).label("portfolio_count"),
        )
        .outerjoin(FloorPlan, FloorPlan.unit_type_id == UnitType.id)
        .outerjoin(Portfolio, Portfolio.unit_type_id == UnitType.id)
        .where(UnitType.complex_id == complex_id)
        .group_by(UnitType.id)
        .order_by(UnitType.exclusive_area_m2.asc(), UnitType.type_code.asc())
    ).all()

    return ComplexDetailResponse(
        complex_id=complex_row.id,
        name=complex_row.name,
        address=complex_row.address,
        built_year=complex_row.built_year,
        household_count=complex_row.household_count,
        unit_types=[
            UnitTypeChip(
                unit_type_id=row.id,
                exclusive_area_m2=row.exclusive_area_m2,
                type_code=row.type_code,
                room_count=row.room_count,
                bathroom_count=row.bathroom_count,
                structure_keyword=row.structure_keyword,
                floor_plan_image_url=row.floor_plan_image_url,
                portfolio_count=row.portfolio_count,
            )
            for row in type_rows
        ],
    )


def list_portfolios(
    db: Session,
    complex_id: int,
    unit_type_id: int | None,
    query: PortfolioFilterQuery,
) -> PortfolioListResponse:
    conditions = [Portfolio.complex_id == complex_id]

    if unit_type_id is not None:
        conditions.append(Portfolio.unit_type_id == unit_type_id)

    if query.min_area is not None:
        conditions.append(UnitType.exclusive_area_m2 >= query.min_area)
    if query.max_area is not None:
        conditions.append(UnitType.exclusive_area_m2 <= query.max_area)
    if query.budget_min_krw is not None:
        conditions.append(Portfolio.budget_max_krw >= query.budget_min_krw)
    if query.budget_max_krw is not None:
        conditions.append(Portfolio.budget_min_krw <= query.budget_max_krw)
    if query.work_scope is not None:
        conditions.append(Portfolio.work_scope == query.work_scope)
    if query.style is not None:
        conditions.append(Portfolio.style == query.style)

    base_stmt = (
        select(
            Portfolio.id,
            Portfolio.title,
            Portfolio.before_image_url,
            Portfolio.after_image_url,
            Portfolio.work_scope,
            Portfolio.style,
            Portfolio.budget_min_krw,
            Portfolio.budget_max_krw,
            Portfolio.duration_days,
            Vendor.id.label("vendor_id"),
            Vendor.name.label("vendor_name"),
        )
        .select_from(Portfolio)
        .join(UnitType, UnitType.id == Portfolio.unit_type_id)
        .outerjoin(Vendor, Vendor.id == Portfolio.vendor_id)
        .where(and_(*conditions))
    )

    total = db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()

    rows = db.execute(
        base_stmt
        .order_by(Portfolio.created_at.desc(), Portfolio.id.desc())
        .limit(query.limit)
        .offset(query.offset)
    ).all()

    items: list[PortfolioCard] = []
    for row in rows:
        before_x, before_y, after_x, after_y = _compute_floor_plan_pins(row.id)
        items.append(
            PortfolioCard(
                portfolio_id=row.id,
                title=row.title,
                before_image_url=row.before_image_url,
                after_image_url=row.after_image_url,
                floor_plan_before_x=before_x,
                floor_plan_before_y=before_y,
                floor_plan_after_x=after_x,
                floor_plan_after_y=after_y,
                work_scope=row.work_scope,
                style=row.style,
                budget_min_krw=row.budget_min_krw,
                budget_max_krw=row.budget_max_krw,
                duration_days=row.duration_days,
                vendor_id=row.vendor_id,
                vendor_name=row.vendor_name,
            )
        )

    return PortfolioListResponse(total=total, items=items)
