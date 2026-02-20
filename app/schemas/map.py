from decimal import Decimal

from pydantic import BaseModel, Field


class MapBoundsQuery(BaseModel):
    south: float = Field(..., ge=-90, le=90)
    west: float = Field(..., ge=-180, le=180)
    north: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    zoom: int = Field(..., ge=0, le=22)


class ComplexPin(BaseModel):
    complex_id: int
    name: str
    latitude: Decimal
    longitude: Decimal
    portfolio_count: int
    distance_m: float | None = None


class ClusterPin(BaseModel):
    cluster_key: str
    center_latitude: Decimal
    center_longitude: Decimal
    count: int


class MapPinsResponse(BaseModel):
    clusters: list[ClusterPin]
    complexes: list[ComplexPin]


class NearbyComplexesResponse(BaseModel):
    center_latitude: float
    center_longitude: float
    radius_m: int
    items: list[ComplexPin]
