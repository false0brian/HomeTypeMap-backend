from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Complex, FloorPlan, FloorPlanPin as FloorPlanPinEntity, FloorPlanPinImage, Portfolio, UnitType, Vendor
from app.schemas.portfolio import (
    ComplexDetailResponse,
    FloorPlanPin,
    PortfolioCard,
    PortfolioFilterQuery,
    PortfolioListResponse,
    UnitTypeChip,
)


def _compute_floor_plan_pin(portfolio_id: int) -> tuple[float, float]:
    # Normalized floor plan position (percentage).
    base_x = 18 + (portfolio_id * 17 % 64)
    base_y = 16 + (portfolio_id * 13 % 66)
    return float(min(92, base_x + 3)), float(min(92, base_y + 2))


def _sample_image_urls(portfolio_id: int, side: str, pin_idx: int) -> list[str]:
    palette = "f4efe8/3f3a34" if side == "before" else "e8f4eb/254739"
    return [
        f"https://placehold.co/960x640/{palette}?text={side.title()}+P{portfolio_id}-{pin_idx + 1}-1",
        f"https://placehold.co/960x640/{palette}?text={side.title()}+P{portfolio_id}-{pin_idx + 1}-2",
        f"https://placehold.co/960x640/{palette}?text={side.title()}+P{portfolio_id}-{pin_idx + 1}-3",
    ]


def _build_floor_plan_pins(portfolio_id: int, before_url: str | None, after_url: str | None) -> list[FloorPlanPin]:
    base_x, base_y = _compute_floor_plan_pin(portfolio_id)
    pins: list[FloorPlanPin] = []
    for pin_idx in range(2):
        x = min(94.0, base_x + pin_idx * 7.0)
        y = min(94.0, base_y + pin_idx * 5.0)
        before_images = _sample_image_urls(portfolio_id, "before", pin_idx)
        after_images = _sample_image_urls(portfolio_id, "after", pin_idx)
        if pin_idx == 0:
            if before_url:
                before_images[0] = before_url
            if after_url:
                after_images[0] = after_url
        pins.append(
            FloorPlanPin(
                pin_id=f"{portfolio_id}-pin-{pin_idx + 1}",
                x=x,
                y=y,
                title=f"포인트 {pin_idx + 1}",
                before_image_urls=before_images,
                after_image_urls=after_images,
            )
        )
    return pins


def _load_db_floor_plan_pins(db: Session, portfolio_ids: list[int]) -> dict[int, list[FloorPlanPin]]:
    if not portfolio_ids:
        return {}

    rows = db.execute(
        select(
            FloorPlanPinEntity.id.label("pin_id"),
            FloorPlanPinEntity.portfolio_id,
            FloorPlanPinEntity.x_ratio,
            FloorPlanPinEntity.y_ratio,
            FloorPlanPinEntity.title,
            FloorPlanPinEntity.sort_order.label("pin_sort_order"),
            FloorPlanPinImage.image_side,
            FloorPlanPinImage.image_url,
            FloorPlanPinImage.sort_order.label("image_sort_order"),
            FloorPlanPinImage.id.label("image_id"),
        )
        .select_from(FloorPlanPinEntity)
        .outerjoin(FloorPlanPinImage, FloorPlanPinImage.floor_plan_pin_id == FloorPlanPinEntity.id)
        .where(FloorPlanPinEntity.portfolio_id.in_(portfolio_ids))
        .order_by(
            FloorPlanPinEntity.portfolio_id.asc(),
            FloorPlanPinEntity.sort_order.asc(),
            FloorPlanPinEntity.id.asc(),
            FloorPlanPinImage.image_side.asc(),
            FloorPlanPinImage.sort_order.asc(),
            FloorPlanPinImage.id.asc(),
        )
    ).all()

    by_portfolio: dict[int, list[FloorPlanPin]] = {}
    pin_cache: dict[int, FloorPlanPin] = {}

    for row in rows:
        pin = pin_cache.get(row.pin_id)
        if pin is None:
            pin = FloorPlanPin(
                pin_id=f"{row.portfolio_id}-pin-{row.pin_id}",
                x=float(row.x_ratio),
                y=float(row.y_ratio),
                title=row.title,
                before_image_urls=[],
                after_image_urls=[],
            )
            pin_cache[row.pin_id] = pin
            by_portfolio.setdefault(row.portfolio_id, []).append(pin)

        if row.image_url:
            if row.image_side == "before":
                pin.before_image_urls.append(row.image_url)
            elif row.image_side == "after":
                pin.after_image_urls.append(row.image_url)

    return by_portfolio


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

    portfolio_ids = [row.id for row in rows]
    db_pins_by_portfolio = _load_db_floor_plan_pins(db, portfolio_ids)

    items: list[PortfolioCard] = []
    for row in rows:
        floor_plan_pins = db_pins_by_portfolio.get(row.id)
        if not floor_plan_pins:
            floor_plan_pins = _build_floor_plan_pins(row.id, row.before_image_url, row.after_image_url)

        before_urls = floor_plan_pins[0].before_image_urls if floor_plan_pins else ([row.before_image_url] if row.before_image_url else [])
        after_urls = floor_plan_pins[0].after_image_urls if floor_plan_pins else ([row.after_image_url] if row.after_image_url else [])
        pin_x = floor_plan_pins[0].x if floor_plan_pins else _compute_floor_plan_pin(row.id)[0]
        pin_y = floor_plan_pins[0].y if floor_plan_pins else _compute_floor_plan_pin(row.id)[1]
        items.append(
            PortfolioCard(
                portfolio_id=row.id,
                title=row.title,
                before_image_url=row.before_image_url,
                after_image_url=row.after_image_url,
                before_image_urls=before_urls,
                after_image_urls=after_urls,
                floor_plan_pin_x=pin_x,
                floor_plan_pin_y=pin_y,
                floor_plan_pins=floor_plan_pins,
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
