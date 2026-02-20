# Repo Sync Policy (Backend)

## 목적
- backend 단독 저장소와 frontend 저장소 간 API 계약 일관성 유지

## 원칙
- API 스키마/비즈니스 로직은 backend repo가 source of truth
- frontend는 backend 계약을 소비하며, 자체 임의 확장 금지

## 운영 규칙
1. API 변경 분류
- non-breaking: optional 필드 추가/신규 endpoint
- breaking: 기존 필드 삭제/의미 변경 -> `/api/v2`로 분리

2. PR 규칙
- backend PR에 `API Change: non-breaking|breaking` 명시
- breaking이면 frontend 대응 PR 링크 동시 첨부

3. 동기화 체크
- backend 머지 후 frontend에서 최소 1회 계약 반영 PR 수행
- 릴리스 노트에 영향 endpoint 표기

4. 릴리스 태그
- backend 태그 예시: `backend-v1.4.0`

## 예외
- 긴급 보안 패치는 선배포 가능하나, 이후 계약 문서/SDK 동기화 필수
