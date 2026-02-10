# BenchHub Plus TODO

## 1. 사용자 흐름과 UI 정합성
- [X] **Reflex Evaluate 플로우를 `/api/v1/leaderboard/generate`에 연결**  
  - [X] 현재 `apps/reflex_frontend/reflex_frontend/reflex_frontend.py` 의 `submit_evaluation()`은 `/hret/evaluate`에 `plan_yaml` 없이 POST하여 422/500을 유발함 (433~438행).  
  - [X] Planner 에이전트가 생성한 `plan_yaml`(또는 서버에서 생성한 값)을 포함하도록 요청 구조를 재설계하고, 성공 시 Task ID를 Status 탭과 연동.
- [X] **Status 탭 UX 정리 (수동 Refresh + 요약 카운트 실시간화)**  
  - [X] Status 상단에 Refresh 버튼을 추가해 최신 task 상태를 수동 갱신.  
  - [X] Summary 카드의 Total/Running/Completed/Pending을 `task_history` 기반으로 계산.
- [X] **UI 문구/탭 구조 vs 문서 정리**  
  - [X] 문서는 로그인 없이 Evaluate/Status/Browse/System 탭을 안내하지만 실제 UI는 Login 버튼과 Manager 탭이 있음 (`docs/eng/user-manual.md:14`, `apps/reflex_frontend/reflex_frontend/reflex_frontend.py:551`).  
  - [X] 문서/튜토리얼/스크린샷을 최신 Reflex UX와 일치하도록 업데이트.
- [X] **Leaderboard Filter Results에 자연어 플래너 기반 필터링 추가**  
  - [X] `/api/v1/leaderboard/suggest` 응답으로 필터 자동 적용 및 결과 재조회.  
  - [X] 결과 테이블을 API 스키마 컬럼 기준으로 정렬(언어/과목/태스크/스코어/업데이트).

## 2. 평가 파이프라인 완성
- [X] **Planner fallback이 `plan_yaml`을 생성하도록 수정**  
  - [X] `apps/backend/services/orchestrator.py:271` 의 `_create_fallback_plan` 이 `plan_yaml` 없이 JSON만 반환하여 Celery 작업이 즉시 실패함; 최소한 기본 BenchHub plan YAML을 생성해 포함.
- [O] **HRET 실행 의존성 정리**  
  - [O] `apps/worker/hret_runner.py` 는 `haerae-evaluation-toolkit (llm_eval)` 미설치 시 RuntimeError 발생. `pyproject.toml` 의 주석 처리된 의존성을 복구하거나 대체 실행기를 번들링.  
  - [O] `Dockerfile.worker` 와 배포 스크립트에 필요한 OS 패키지/모델 가중치 준비 단계 추가.
- [X] **결과 저장 로직 구현**  
  - [X] HRET 결과(`HRETResultMapper`)를 통해 ExperimentSample / LeaderboardCache에 저장하도록 통합.  
  - [X] Runner → Mapper → Storage 파이프라인을 연결하고 task_id 연동.

## 3. 데이터 시딩 및 영속성
- [X] **동적 데이터 소스 도입**  
  - [X] 앱 시작 시마다 `apps/backend/seeding.py` 가 `data/seed_data.parquet` 를 요구하지만 리포지토리엔 파일이 없음. 실제 데이터 소스(객체 스토리지, API 등)를 구성하거나 시딩 조건을 비활성/옵션화.  
  - [X] 대규모 데이터 입력 시 `upsert_entry()` 가 각 행마다 커밋 → 성능 저하. 벌크 트랜잭션 지원 추가 검토.
- [X] **마이그레이션 전략 수립**  
  - [X] `scripts/deploy.sh:127` 는 항상 `init_db()` 를 실행하여 `CREATE TABLE IF NOT EXISTS` 수준만 수행. Alembic 등을 도입해 SaaS 운영 중 스키마 변경을 안전하게 적용.  
  - [X] 배포 전 백업/롤백 절차와 모니터링 체크리스트 문서화.

## 4. 인증/권한 구조
- [X] **다중 테넌트 대비 사용자 스키마 확장**  
  - [X] 현재 `users` 테이블은 `google_id/role/is_admin` 만 존재 (`apps/core/db.py:47`). 구독형 SaaS 를 위해 조직, 워크스페이스, 역할 기반 권한(RBAC) 메타데이터를 추가.  
  - [X] Manager/Tasks/Audit API 가 전부 관리자 전용 (`apps/backend/routes/status.py:223`, `apps/backend/routes/manager.py:39`). 일반 사용자가 자신의 작업/리더보드 상태를 볼 수 있도록 권한 세분화.
- [X] **Frontend 로그인 UX 개선**  
  - [X] `AppState.start_google_login()` 으로만 인증을 제공하며 실패 시 안내 메시지가 없음 (`apps/reflex_frontend/reflex_frontend/reflex_frontend.py:210`). OAuth 흐름 에러 처리, 토큰 만료 시 재로그인 UX 등을 구현.
- [X] **Manager 탭 접근제어 + 로그인 실패/만료 배너 표시**  
  - [X] 비관리자에 대해 Manager 탭 비활성화 및 접근 제한 안내.  
  - [X] 인증 실패/만료 시 상단 배너로 재로그인 안내.

## 5. 문서 & 테스트 정리
- [X] **문서 최신화**  
  - [X] `docs/eng/development.md` 등에서 여전히 Streamlit 기반 아키텍처와 `./scripts/dev-backend.sh` 를 안내. Reflex + FastAPI + Celery 구조를 반영하고, 관리자 전용 기능/Rate limit/OAuth 요구사항을 명시.  
  - [X] `docs/eng/user-manual.md` 의 결과 섹션은 Score/Accuracy/Samples를 제공한다고 하지만 API 스키마엔 해당 필드가 없음 (`apps/core/schemas.py:24`). 문서 또는 API 중 하나를 수정해 일관성 확보.
- [X] **깨진 테스트 수정**  
  - [X] `tests/integration/test_api.py` 는 존재하지 않는 `EvaluationOrchestrator.create_evaluation_task` 를 패치하거나 `LeaderboardCache` 에 없는 컬럼(`accuracy`, `sample_count`)을 사용. 실제 구현에 맞게 테스트 업데이트 및 CI 복구.  
  - [X] Planner/credential/worker 기능에 대한 단위·통합 테스트 추가로 회귀 방지.

## 6. 모니터링 및 운영
- [X] **Manager/Status 데이터 완성**  
  - [X] 현재 Manager 대시보드는 `apps/reflex_frontend/reflex_frontend/reflex_frontend.py:225` 의 `refresh_manager_snapshot()` 에서 API 응답을 화면에 반영하지만, 서버 측 `/api/v1/manager/snapshot` 은 관리자 토큰 없이는 접근 불가. 고객용 모니터링 경로를 설계하고, 관리자/고객 UI를 분리.  
  - [X] Celery/Redis/DB 상태가 비정상일 때 자동 재시도나 경고 채널(Slack/Webhook 등)을 추가.

---
각 항목별로 우선순위(P0/P1 등)와 일정, 담당자를 지정하여 스프린트 계획에 반영하세요.
