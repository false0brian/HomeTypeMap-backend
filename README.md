# HomeTypeMap Backend

HomeTypeMap API 서버 저장소입니다.
FastAPI + SQLAlchemy + Alembic + PostgreSQL(PostGIS) 기반입니다.

## Run (Local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_mvp.py
uvicorn app.main:app --reload
```

API 문서:
- Swagger: `http://127.0.0.1:8000/docs`

## Run (Docker)
```bash
docker compose up --build
```

## Test
```bash
pytest -q
```

## Key Paths
- `app/`: FastAPI app
- `alembic/`: migration
- `scripts/`: seed/openapi export
- `tests/`: backend tests
- `docs/api-contract.md`: API 계약 문서

## API Version Policy
- 기본 경로: `/api/v1`
- breaking change는 `/api/v2`로 분리

## Sync Policy
- 모노레포/프론트 저장소와 동기화 규칙은 `docs/repo-sync-policy.md` 참고
