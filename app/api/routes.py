from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.schemas.admin import (
    AdminBlogPostCreate,
    AdminBlogPostResponse,
    AdminBlogPostUpdate,
    AdminPortfolioCreate,
    AdminPortfolioResponse,
    AdminPortfolioUpdate,
    PublishStatus,
)
from app.schemas.map import MapBoundsQuery, MapPinsResponse, NearbyComplexesResponse
from app.schemas.portfolio import (
    ComplexDetailResponse,
    FavoriteCreateRequest,
    FavoriteResponse,
    PortfolioFilterQuery,
    PortfolioListResponse,
    WorkScopeType,
)
from app.schemas.vendor import QuoteRequestCreate, QuoteRequestResponse
from app.services.favorite_service import create_favorite, list_favorites
from app.services.map_service import get_map_pins, get_nearby_complexes
from app.services.admin_service import (
    create_admin_portfolio,
    create_blog_post,
    list_admin_portfolios,
    list_blog_posts,
    update_admin_portfolio,
    update_blog_post,
)
from app.services.portfolio_service import get_complex_detail, list_portfolios
from app.services.quote_service import create_quote_request

router = APIRouter(prefix="/api/v1")


def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="invalid admin key")


admin_router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_key)],
)


@router.get(
    "/map/pins",
    response_model=MapPinsResponse,
    tags=["map"],
    summary="지도 범위 내 단지 핀 또는 클러스터 조회",
)
def map_pins(
    south: float = Query(..., description="지도 하단 위도", examples=[37.4]),
    west: float = Query(..., description="지도 좌측 경도", examples=[127.0]),
    north: float = Query(..., description="지도 상단 위도", examples=[37.6]),
    east: float = Query(..., description="지도 우측 경도", examples=[127.2]),
    zoom: int = Query(..., ge=0, le=22, description="클라이언트 지도 줌 레벨", examples=[13]),
    db: Session = Depends(get_db),
):
    bounds = MapBoundsQuery(south=south, west=west, north=north, east=east, zoom=zoom)
    return get_map_pins(db, bounds)


@router.get(
    "/map/nearby",
    response_model=NearbyComplexesResponse,
    tags=["map"],
    summary="현재 위치 기준 반경 내 단지 조회",
)
def map_nearby(
    lat: float = Query(..., ge=-90, le=90, description="기준 위도"),
    lng: float = Query(..., ge=-180, le=180, description="기준 경도"),
    radius_m: int = Query(default=3000, ge=200, le=50000, description="검색 반경(미터)"),
    limit: int = Query(default=200, ge=1, le=1000, description="최대 반환 개수"),
    db: Session = Depends(get_db),
):
    return get_nearby_complexes(db, latitude=lat, longitude=lng, radius_m=radius_m, limit=limit)


@router.get(
    "/complexes/{complex_id}",
    response_model=ComplexDetailResponse,
    tags=["complex"],
    summary="단지 상세와 평형 타입 칩 조회",
)
def complex_detail(complex_id: int, db: Session = Depends(get_db)):
    detail = get_complex_detail(db, complex_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="complex not found")
    return detail


@router.get(
    "/complexes/{complex_id}/portfolios",
    response_model=PortfolioListResponse,
    tags=["complex"],
    summary="타입별 포트폴리오 리스트 조회",
)
def complex_portfolios(
    complex_id: int,
    unit_type_id: int | None = Query(default=None, description="평형 타입 ID", examples=[1001]),
    min_area: float | None = Query(default=None, ge=0, description="전용면적 최소(m2)", examples=[59]),
    max_area: float | None = Query(default=None, ge=0, description="전용면적 최대(m2)", examples=[84]),
    budget_min_krw: int | None = Query(default=None, ge=0, description="예산 하한(원)", examples=[30000000]),
    budget_max_krw: int | None = Query(default=None, ge=0, description="예산 상한(원)", examples=[50000000]),
    work_scope: WorkScopeType | None = Query(default=None, description="공사 범위"),
    style: str | None = Query(default=None, description="스타일 키워드", examples=["minimal"]),
    limit: int = Query(default=30, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(default=0, ge=0, description="페이지 오프셋"),
    db: Session = Depends(get_db),
):
    filters = PortfolioFilterQuery(
        min_area=min_area,
        max_area=max_area,
        budget_min_krw=budget_min_krw,
        budget_max_krw=budget_max_krw,
        work_scope=work_scope,
        style=style,
        limit=limit,
        offset=offset,
    )
    return list_portfolios(db, complex_id=complex_id, unit_type_id=unit_type_id, query=filters)


@router.post(
    "/favorites",
    response_model=FavoriteResponse,
    status_code=201,
    tags=["favorite"],
    summary="포트폴리오 즐겨찾기 저장",
)
def favorite_create(payload: FavoriteCreateRequest, db: Session = Depends(get_db)):
    row = create_favorite(db, user_key=payload.user_key, portfolio_id=payload.portfolio_id)
    return FavoriteResponse(favorite_id=row.id, user_key=row.user_key, portfolio_id=row.portfolio_id)


@router.get(
    "/favorites",
    response_model=list[FavoriteResponse],
    tags=["favorite"],
    summary="사용자 즐겨찾기 조회",
)
def favorite_list(user_key: str = Query(...), db: Session = Depends(get_db)):
    rows = list_favorites(db, user_key=user_key)
    return [
        FavoriteResponse(favorite_id=row.id, user_key=row.user_key, portfolio_id=row.portfolio_id)
        for row in rows
    ]


@router.post(
    "/quote-requests",
    response_model=QuoteRequestResponse,
    status_code=201,
    tags=["quote"],
    summary="업체 문의/견적 요청 생성",
)
def quote_request_create(payload: QuoteRequestCreate, db: Session = Depends(get_db)):
    row = create_quote_request(
        db,
        user_key=payload.user_key,
        vendor_id=payload.vendor_id,
        portfolio_id=payload.portfolio_id,
        preferred_date=payload.preferred_date,
        message=payload.message,
    )
    return QuoteRequestResponse(
        quote_request_id=row.id,
        user_key=row.user_key,
        vendor_id=row.vendor_id,
        portfolio_id=row.portfolio_id,
    )


@admin_router.get(
    "/portfolios",
    response_model=list[AdminPortfolioResponse],
    summary="관리자 포트폴리오 목록 조회",
)
def admin_portfolio_list(
    vendor_id: int | None = Query(default=None),
    status: PublishStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    rows = list_admin_portfolios(db, vendor_id=vendor_id, status=status, limit=limit, offset=offset)
    return [
        AdminPortfolioResponse(
            portfolio_id=row.id,
            complex_id=row.complex_id,
            unit_type_id=row.unit_type_id,
            vendor_id=row.vendor_id,
            title=row.title,
            work_scope=row.work_scope,
            style=row.style,
            status=row.status,
            budget_min_krw=row.budget_min_krw,
            budget_max_krw=row.budget_max_krw,
            duration_days=row.duration_days,
            published_at=row.published_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


@admin_router.post(
    "/portfolios",
    response_model=AdminPortfolioResponse,
    status_code=201,
    summary="관리자 포트폴리오 생성",
)
def admin_portfolio_create(payload: AdminPortfolioCreate, db: Session = Depends(get_db)):
    row = create_admin_portfolio(db, payload)
    return AdminPortfolioResponse(
        portfolio_id=row.id,
        complex_id=row.complex_id,
        unit_type_id=row.unit_type_id,
        vendor_id=row.vendor_id,
        title=row.title,
        work_scope=row.work_scope,
        style=row.style,
        status=row.status,
        budget_min_krw=row.budget_min_krw,
        budget_max_krw=row.budget_max_krw,
        duration_days=row.duration_days,
        published_at=row.published_at,
        created_at=row.created_at,
    )


@admin_router.patch(
    "/portfolios/{portfolio_id}",
    response_model=AdminPortfolioResponse,
    summary="관리자 포트폴리오 수정",
)
def admin_portfolio_patch(portfolio_id: int, payload: AdminPortfolioUpdate, db: Session = Depends(get_db)):
    row = update_admin_portfolio(db, portfolio_id=portfolio_id, payload=payload)
    if row is None:
        raise HTTPException(status_code=404, detail="portfolio not found")
    return AdminPortfolioResponse(
        portfolio_id=row.id,
        complex_id=row.complex_id,
        unit_type_id=row.unit_type_id,
        vendor_id=row.vendor_id,
        title=row.title,
        work_scope=row.work_scope,
        style=row.style,
        status=row.status,
        budget_min_krw=row.budget_min_krw,
        budget_max_krw=row.budget_max_krw,
        duration_days=row.duration_days,
        published_at=row.published_at,
        created_at=row.created_at,
    )


@admin_router.get(
    "/blog-posts",
    response_model=list[AdminBlogPostResponse],
    summary="관리자 블로그 글 목록 조회",
)
def admin_blog_list(
    vendor_id: int | None = Query(default=None),
    status: PublishStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    rows = list_blog_posts(db, vendor_id=vendor_id, status=status, limit=limit, offset=offset)
    return [
        AdminBlogPostResponse(
            post_id=row.id,
            vendor_id=row.vendor_id,
            title=row.title,
            slug=row.slug,
            excerpt=row.excerpt,
            content=row.content,
            status=row.status,
            published_at=row.published_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@admin_router.post(
    "/blog-posts",
    response_model=AdminBlogPostResponse,
    status_code=201,
    summary="관리자 블로그 글 생성",
)
def admin_blog_create(payload: AdminBlogPostCreate, db: Session = Depends(get_db)):
    row = create_blog_post(db, payload)
    return AdminBlogPostResponse(
        post_id=row.id,
        vendor_id=row.vendor_id,
        title=row.title,
        slug=row.slug,
        excerpt=row.excerpt,
        content=row.content,
        status=row.status,
        published_at=row.published_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@admin_router.patch(
    "/blog-posts/{post_id}",
    response_model=AdminBlogPostResponse,
    summary="관리자 블로그 글 수정",
)
def admin_blog_patch(post_id: int, payload: AdminBlogPostUpdate, db: Session = Depends(get_db)):
    row = update_blog_post(db, post_id=post_id, payload=payload)
    if row is None:
        raise HTTPException(status_code=404, detail="blog post not found")
    return AdminBlogPostResponse(
        post_id=row.id,
        vendor_id=row.vendor_id,
        title=row.title,
        slug=row.slug,
        excerpt=row.excerpt,
        content=row.content,
        status=row.status,
        published_at=row.published_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


router.include_router(admin_router)
