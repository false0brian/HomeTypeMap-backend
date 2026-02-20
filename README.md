# HomeTypeMap

지도에서 단지/주택을 선택하고, 평형 타입별 인테리어 포트폴리오를 탐색하는 MVP입니다.
백엔드(FastAPI) + 프론트(React) 모노레포 구조입니다.

## 핵심 기능
- 지도 핀/클러스터 조회: `GET /api/v1/map/pins`
- 현재 위치 주변 단지 조회: `GET /api/v1/map/nearby`
- 단지 상세 + 타입 칩: `GET /api/v1/complexes/{complex_id}`
- 타입별 포트폴리오 + 필터: `GET /api/v1/complexes/{complex_id}/portfolios`
- 즐겨찾기: `POST /api/v1/favorites`, `GET /api/v1/favorites`
- 견적 요청: `POST /api/v1/quote-requests`

핵심 매칭 키:
- `portfolios.complex_id`
- `portfolios.unit_type_id`

## 저장소 구조
- `app/`: FastAPI 앱
- `alembic/`: DB 마이그레이션
- `frontend/`: React(Vite+TS, Leaflet + OpenStreetMap)
- `sql/`: 참고 DDL/샘플 SQL
- `docs/`: API 계약/와이어프레임 문서
- `tests/`: 백엔드 테스트

## 1) Docker로 실행 (추천)
필수: Docker / Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

접속 주소:
- 프론트: `http://127.0.0.1:5173`
- 관리자 콘솔: `http://127.0.0.1:5173/admin`
- 백엔드 Swagger: `http://127.0.0.1:8000/docs`
- PostgreSQL: `localhost:5432` (`postgres/postgres`)

구성:
- `db` (PostGIS 포함 PostgreSQL 16)
- `backend` (Alembic 적용 + 시드 입력 후 uvicorn 실행)
- `frontend` (React 빌드 결과를 nginx로 서빙, `/api`를 backend로 프록시)

## 2) 로컬로 실행
### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_mvp.py
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

기본 프론트 주소: `http://127.0.0.1:5173`

## 테스트
```bash
pytest -q
```

## API 계약/참고 문서
- API 계약: `docs/api-contract.md`
- 와이어프레임: `docs/frontend/wireframe.md`
- HTML 샘플: `docs/frontend/map_bottom_sheet_example.html`
- RN 샘플: `docs/frontend/react_native_integration_example.ts`
- Flutter 연동 노트: `docs/frontend/flutter_integration_notes.md`

## 관리자 API 인증
- 헤더 `X-Admin-Key`가 필요합니다.
- 기본 개발 키: `.env.example`의 `ADMIN_API_KEY=dev-admin-key`

## 사용성 개선 반영 사항
1. 사용자 식별 입력 방식
- 기존: 액션마다 `window.prompt`로 `user_key` 입력
- 변경: 상단 고정 입력 필드(`user_key`)로 통일

2. 필터 반영 타이밍
- 기존: 입력 타이핑 즉시 API 재호출
- 변경: `필터 적용` 버튼으로 명시적 반영 + `필터 초기화` 제공

3. 상태 피드백
- 기존: 에러/로딩 메시지가 분산
- 변경: 상단 `status` 바에 현재 상태를 집중 노출

4. 현재 위치 기반 근처 보기
- 브라우저 위치 권한 허용 시 `내 위치 주변` 버튼으로 반경 검색
- 기본 반경 프리셋: `1km / 3km / 5km`

## OpenAPI export
```bash
python scripts/export_openapi.py
```
결과: `docs/openapi.json`

## 트러블슈팅
1. `pip install` / `npm install`이 실패하는 경우
- 증상: DNS 오류(`EAI_AGAIN`, `Name or service not known`)
- 원인: 실행 환경 네트워크 제한
- 조치: 인터넷 가능한 환경에서 설치하거나 사내 미러 레지스트리 사용

2. 포트 충돌
- `5432`, `8000`, `5173` 사용 중이면 `docker-compose.yml` 포트 변경

3. 지도가 비어있게 보이는 경우
- 브라우저 콘솔에서 타일 요청 에러 확인
- 네트워크에서 `tile.openstreetmap.org` 접근 가능 여부 확인
