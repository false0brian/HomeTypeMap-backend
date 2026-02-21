from sqlalchemy import Select, exists, func, select
from sqlalchemy.orm import Session, aliased

from app.models import Complex, Portfolio, UnitType
from app.schemas.map import ClusterPin, ComplexPin, MapBoundsQuery, MapPinsResponse, NearbyComplexesResponse


def _bbox_base_query(bounds: MapBoundsQuery) -> Select:
    return (
        select(Complex)
        .where(Complex.centroid_latitude >= bounds.south)
        .where(Complex.centroid_latitude <= bounds.north)
        .where(Complex.centroid_longitude >= bounds.west)
        .where(Complex.centroid_longitude <= bounds.east)
    )


def _complex_filter_exists(
    vendor_id: int | None = None,
    work_scope: str | None = None,
    min_area: float | None = None,
):
    if vendor_id is None and work_scope is None and min_area is None:
        return None

    p = aliased(Portfolio)
    u = aliased(UnitType)
    stmt = select(1).select_from(p).join(u, u.id == p.unit_type_id).where(p.complex_id == Complex.id)
    if vendor_id is not None:
        stmt = stmt.where(p.vendor_id == vendor_id)
    if work_scope is not None:
        stmt = stmt.where(p.work_scope == work_scope)
    if min_area is not None:
        stmt = stmt.where(u.exclusive_area_m2 >= min_area)
    return exists(stmt)


def get_map_pins(
    db: Session,
    bounds: MapBoundsQuery,
    vendor_id: int | None = None,
    work_scope: str | None = None,
    min_area: float | None = None,
) -> MapPinsResponse:
    complex_filter_exists = _complex_filter_exists(vendor_id=vendor_id, work_scope=work_scope, min_area=min_area)

    if bounds.zoom <= 11:
        precision = 2 if bounds.zoom <= 8 else 3
        lat_bucket = func.round(Complex.centroid_latitude, precision)
        lng_bucket = func.round(Complex.centroid_longitude, precision)

        stmt = (
            select(
                lat_bucket.label("lat_bucket"),
                lng_bucket.label("lng_bucket"),
                func.count(Complex.id).label("count"),
            )
            .select_from(Complex)
            .where(Complex.centroid_latitude >= bounds.south)
            .where(Complex.centroid_latitude <= bounds.north)
            .where(Complex.centroid_longitude >= bounds.west)
            .where(Complex.centroid_longitude <= bounds.east)
        )
        if complex_filter_exists is not None:
            stmt = stmt.where(complex_filter_exists)

        rows = db.execute(
            stmt.group_by(lat_bucket, lng_bucket).order_by(func.count(Complex.id).desc()).limit(300)
        ).all()

        return MapPinsResponse(
            clusters=[
                ClusterPin(
                    cluster_key=f"{row.lat_bucket}:{row.lng_bucket}",
                    center_latitude=row.lat_bucket,
                    center_longitude=row.lng_bucket,
                    count=row.count,
                )
                for row in rows
            ],
            complexes=[],
        )

    count_filters = []
    if vendor_id is not None:
        count_filters.append(Portfolio.vendor_id == vendor_id)
    if work_scope is not None:
        count_filters.append(Portfolio.work_scope == work_scope)
    if min_area is not None:
        count_filters.append(UnitType.exclusive_area_m2 >= min_area)
    portfolio_count_expr = (
        func.count(Portfolio.id)
        if not count_filters
        else func.count(Portfolio.id).filter(*count_filters)
    )
    stmt = (
        select(
            Complex.id,
            Complex.name,
            Complex.centroid_latitude,
            Complex.centroid_longitude,
            portfolio_count_expr.label("portfolio_count"),
        )
        .outerjoin(Portfolio, Portfolio.complex_id == Complex.id)
        .outerjoin(UnitType, UnitType.id == Portfolio.unit_type_id)
        .where(Complex.centroid_latitude >= bounds.south)
        .where(Complex.centroid_latitude <= bounds.north)
        .where(Complex.centroid_longitude >= bounds.west)
        .where(Complex.centroid_longitude <= bounds.east)
        .group_by(Complex.id)
    )
    if count_filters:
        stmt = stmt.having(portfolio_count_expr > 0)
    rows = db.execute(stmt.order_by(portfolio_count_expr.desc(), Complex.id).limit(1000)).all()

    return MapPinsResponse(
        clusters=[],
        complexes=[
            ComplexPin(
                complex_id=row.id,
                name=row.name,
                latitude=row.centroid_latitude,
                longitude=row.centroid_longitude,
                portfolio_count=row.portfolio_count,
            )
            for row in rows
        ],
    )


def get_nearby_complexes(
    db: Session,
    latitude: float,
    longitude: float,
    radius_m: int,
    limit: int = 200,
    vendor_id: int | None = None,
    work_scope: str | None = None,
    min_area: float | None = None,
) -> NearbyComplexesResponse:
    earth_radius_m = 6371000
    distance_expr = earth_radius_m * func.acos(
        func.least(
            1.0,
            func.greatest(
                -1.0,
                func.sin(func.radians(latitude)) * func.sin(func.radians(Complex.centroid_latitude))
                + func.cos(func.radians(latitude))
                * func.cos(func.radians(Complex.centroid_latitude))
                * func.cos(func.radians(Complex.centroid_longitude) - func.radians(longitude)),
            ),
        )
    )

    count_filters = []
    if vendor_id is not None:
        count_filters.append(Portfolio.vendor_id == vendor_id)
    if work_scope is not None:
        count_filters.append(Portfolio.work_scope == work_scope)
    if min_area is not None:
        count_filters.append(UnitType.exclusive_area_m2 >= min_area)
    portfolio_count_expr = (
        func.count(Portfolio.id)
        if not count_filters
        else func.count(Portfolio.id).filter(*count_filters)
    )
    stmt = (
        select(
            Complex.id,
            Complex.name,
            Complex.centroid_latitude,
            Complex.centroid_longitude,
            portfolio_count_expr.label("portfolio_count"),
            distance_expr.label("distance_m"),
        )
        .outerjoin(Portfolio, Portfolio.complex_id == Complex.id)
        .outerjoin(UnitType, UnitType.id == Portfolio.unit_type_id)
        .group_by(Complex.id)
        .having(distance_expr <= radius_m)
    )
    if count_filters:
        stmt = stmt.having(portfolio_count_expr > 0)
    rows = db.execute(stmt.order_by(distance_expr.asc(), Complex.id.asc()).limit(limit)).all()

    return NearbyComplexesResponse(
        center_latitude=latitude,
        center_longitude=longitude,
        radius_m=radius_m,
        items=[
            ComplexPin(
                complex_id=row.id,
                name=row.name,
                latitude=row.centroid_latitude,
                longitude=row.centroid_longitude,
                portfolio_count=row.portfolio_count,
                distance_m=float(row.distance_m),
            )
            for row in rows
        ],
    )
