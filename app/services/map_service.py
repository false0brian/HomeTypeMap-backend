from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Complex, Portfolio
from app.schemas.map import ClusterPin, ComplexPin, MapBoundsQuery, MapPinsResponse, NearbyComplexesResponse


def _bbox_base_query(bounds: MapBoundsQuery) -> Select:
    return (
        select(Complex)
        .where(Complex.centroid_latitude >= bounds.south)
        .where(Complex.centroid_latitude <= bounds.north)
        .where(Complex.centroid_longitude >= bounds.west)
        .where(Complex.centroid_longitude <= bounds.east)
    )


def get_map_pins(db: Session, bounds: MapBoundsQuery) -> MapPinsResponse:
    if bounds.zoom <= 11:
        precision = 2 if bounds.zoom <= 8 else 3
        lat_bucket = func.round(Complex.centroid_latitude, precision)
        lng_bucket = func.round(Complex.centroid_longitude, precision)

        rows = db.execute(
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
            .group_by(lat_bucket, lng_bucket)
            .order_by(func.count(Complex.id).desc())
            .limit(300)
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

    rows = db.execute(
        select(
            Complex.id,
            Complex.name,
            Complex.centroid_latitude,
            Complex.centroid_longitude,
            func.count(Portfolio.id).label("portfolio_count"),
        )
        .outerjoin(Portfolio, Portfolio.complex_id == Complex.id)
        .where(Complex.centroid_latitude >= bounds.south)
        .where(Complex.centroid_latitude <= bounds.north)
        .where(Complex.centroid_longitude >= bounds.west)
        .where(Complex.centroid_longitude <= bounds.east)
        .group_by(Complex.id)
        .order_by(func.count(Portfolio.id).desc(), Complex.id)
        .limit(1000)
    ).all()

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

    rows = db.execute(
        select(
            Complex.id,
            Complex.name,
            Complex.centroid_latitude,
            Complex.centroid_longitude,
            func.count(Portfolio.id).label("portfolio_count"),
            distance_expr.label("distance_m"),
        )
        .outerjoin(Portfolio, Portfolio.complex_id == Complex.id)
        .group_by(Complex.id)
        .having(distance_expr <= radius_m)
        .order_by(distance_expr.asc(), Complex.id.asc())
        .limit(limit)
    ).all()

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
