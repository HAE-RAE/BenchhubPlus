# TODO: Manager Page Backend Tasks

Reflex 프런트엔드 매니저 페이지는 목업 데이터로 동작합니다. 아래 항목들은 실제 운영 데이터를 다룰 수 있도록 백엔드에서 구현되어야 하는 필수/추가 작업들입니다.

## 1. Health & Capacity Snapshot API
- [ ] `/api/v1/health`를 확장해 Redis/HRET/Planner 세부 상태, 버전, 마지막 확인 시각을 포함한다.
- [ ] `/api/v1/stats`에서 대기/실행/성공/실패 작업 수 외에 평균 대기 시간, 최근 15분 처리량, 캐시 엔트리 수를 제공한다.
- [ ] 단일 호출로 Snapshot을 내려주는 전용 엔드포인트(`/api/v1/manager/snapshot`)를 만들고 위의 지표를 한 번에 반환한다.

## 2. Task Pipeline Control
- [ ] `/api/v1/tasks`에 쿼리 파라미터(상태, 사용자, 날짜 범위, 모델 수 등)와 페이지네이션을 추가한다.
- [ ] 개별 작업 상태를 재시작/취소/보류 처리할 수 있는 PATCH endpoint(예: `PATCH /api/v1/tasks/{task_id}`)를 구현한다.
- [ ] “과도한 모델 제출” 등 정책 위반 태그를 기록하고 응답에 포함하기 위한 필드를 DB에 추가한다.
- [ ] 작업 세부 정보(요청 페이로드, 에러 로그)를 반환하는 `/api/v1/tasks/{task_id}/details`를 제공한다.

## 3. Leaderboard Coverage & Moderation
- [ ] `/api/v1/leaderboard/browse` 응답에 엔트리 ID를 포함하고, 단일/복수 엔트리를 삭제할 수 있는 `DELETE /api/v1/leaderboard/{entry_id}` (또는 bulk API)를 제공한다.
- [ ] 관리자 전용 POST `/api/v1/leaderboard/entries`를 만들어 수동으로 점수를 추가하거나 수정할 수 있도록 하고, 입력 검증 로직을 정의한다.
- [ ] 캐시/DB 레이어에서 “quarantine” 상태를 지원하여 숨김 처리와 완전 삭제를 구분한다.
- [ ] 필터 추천(`/api/v1/leaderboard/suggest`) 결과에 신뢰도, 추천 근거를 추가해 UI에서 표시할 수 있도록 한다.

## 4. 인증 및 권한 (선행 조건)
- [ ] 관리자 전용 JWT/세션 기반 인증을 도입하고, 위 관리 API에 Role 기반 접근 제어를 적용한다.
- [ ] 모든 조작 API 호출에 감사 로그를 남기고 `/api/v1/manager/audit`로 조회 가능하게 한다.

## 5. 기타 운영 지원
- [ ] 리더보드/작업 삭제, 재시작 등의 조작 내역을 Slack/Webhook으로 전송하는 알림 훅을 추가한다.
- [ ] HRET 사용 가능 여부, 지원 데이터셋/모델 목록을 반환하는 `/hret/status`, `/hret/config` 응답 스키마를 고정하고 버전 정보를 포함시킨다.
- [ ] 향후 실시간 갱신을 위해 WebSocket/Server-Sent Events 채널을 설계 (우선순위 낮음).

> 위 항목들이 완료되면 Reflex 매니저 페이지에서 실제 데이터를 조회/조작하도록 이벤트 핸들러만 변경하면 됩니다.
