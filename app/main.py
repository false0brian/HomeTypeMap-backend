from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="HomeTypeMap API",
    version="0.1.0",
    openapi_tags=[
        {"name": "map", "description": "지도 핀/클러스터 조회"},
        {"name": "complex", "description": "단지 상세/타입/포트폴리오"},
        {"name": "favorite", "description": "즐겨찾기"},
        {"name": "quote", "description": "견적 요청"},
        {"name": "admin", "description": "관리자 포트폴리오/블로그 관리"},
    ],
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
