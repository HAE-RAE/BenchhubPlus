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
- [X] **HRET 실행 의존성 정리**  
  - [X] `apps/worker/hret_runner.py` 는 `haerae-evaluation-toolkit (llm_eval)` 미설치 시 RuntimeError 발생. `pyproject.toml` 의 주석 처리된 의존성을 복구하거나 대체 실행기를 번들링.  
  - [X] `Dockerfile.worker` 와 배포 스크립트에 필요한 OS 패키지/모델 가중치 준비 단계 추가.
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

## 7. SaaS 출시 잔여 작업 (2026-04-25 추가)

이번 라운드에서 backend hardening / Supabase 호환 / 대화형 평가 워크플로 / Resend풍 디자인 시스템 / 다크모드 / Reflex 프론트엔드 제거를 끝냄. 다음 우선순위는 아래.

### 7.1 멀티테넌시 정식화 (P0)
- [ ] **`ModelCredential` 에 `user_id`/`workspace_id` 컬럼 추가** — 현재 전역 unique hash라 사용자간 자격증명 공유 위험. 마이그레이션 + `credential_service` 변경 필요.  
  - 임시 방편: `apps/backend/routes/dataset.py:recent_models` 에서 비-admin은 본인 task에서만 모델명 추출하도록 막아둔 상태.
- [ ] **모든 list 쿼리에 tenant 필터 강제** — `tasks_repo.filter_tasks(user_id=...)` 패턴을 helper로 통합해 누락 방지.
- [ ] **PostgreSQL Row-Level Security (RLS) 검토** — Supabase로 가는 길이라면 DB 레벨에서도 한 겹 더 막을지 결정. ORM 필터만 둘지 RLS 도 둘지.
- [ ] **`Organization` / `Workspace` 모델은 있으나 사용자가 멤버를 늘릴 UI/API 없음** — 초대, 역할 변경, 워크스페이스 전환 화면 추가.

### 7.2 운영 강화 (P0)
- [ ] **의존성 핀 고정** — `pyproject.toml` 의 `>=` 범위 → 정확한 버전 (`==`) 으로 lock. `pip-tools` / `uv lock` 도입 검토. 프론트도 `package-lock.json` 갱신.
- [ ] **Dependabot / renovate 설정** — CVE 알림 자동화.
- [ ] **시크릿 로테이션** — `JWT_SECRET_KEY`, `SECRET_KEY` 회전 절차. JWT 회전은 `kid` 헤더 + 키 셋 보관 필요.
- [ ] **Celery 메시지 서명 (auth serializer)** — 현재는 Redis AUTH + JSON-only로만 차단. PKI 부트스트랩 후 진짜 서명 추가하면 broker 침투 시에도 코드 실행 차단.
- [ ] **로그 PII redaction** — 이메일 마스킹은 인증 흐름에만 적용됨. 모든 로그 핸들러에 redact 필터 부착.
- [ ] **종합 audit log** — 현재 task delete/launch만 기록. login/logout/token refresh/credential 접근/admin 권한 부여까지 확장.
- [ ] **Sentry / OpenTelemetry 연동** — `request_id` 미들웨어는 있으니 외부 트레이서로 흐름 연결.

### 7.3 평가 파이프라인 안정화 (P1)
- [ ] **`EvaluationDraft` 정리 cron** — `status="abandoned"` 또는 7일 이상 묵은 draft 자동 정리. 현재는 무한 누적.
- [ ] **OpenAI 비용 캡** — 대화 한 번에 tool calling 4 iter × 700 tokens. user별 일일 토큰 한도 체크.
- [ ] **Chat planner 휴리스틱 강화** — placeholder 키 환경에서 슬롯 추출 정확도 낮음. 정규식 기반 한국어/영어 키워드 매칭 추가.
- [ ] **Draft → Task 연결 추적** — 현재 `launched_task_id` 만 저장. 작업 완료 후 draft → result 링크 UI 필요 (chat에 결과 인라인 표시).
- [ ] **모델 추천 시 가격/지연시간 메타데이터** — `suggested_models` 에 토큰 단가/평균 latency 포함하면 사용자가 RUN 전에 비교 가능.

### 7.4 프론트엔드 추가 폴리시 (P1)
- [ ] **`page.tsx` 1294줄 컴포넌트 분리** — `<EvaluationView>`, `<LeaderboardView>`, `<ManagerView>`, `<TaskDetailPanel>` 을 별도 파일로. `useAuth()` 훅 추출.
- [ ] **Toast 시스템** (현재는 자체 Banner) — `sonner` 도입해 알림 스택 / dismiss / undo 액션.
- [ ] **AbortController 도입** — view 전환 시 진행 중인 fetch 취소. 메모리 누수 + race condition 방어.
- [ ] **Skeleton 로더** — leaderboard / manager 표 로딩 중 스피너 대신 shadcn `<Skeleton />`.
- [ ] **Storybook / Visual 테스트** — 디자인 회귀 잡기.
- [ ] **e2e (Playwright)** — auth → draft chat → launch → detail 플로우 회귀 방지.

### 7.5 문서 정리 (P2)
- [ ] **README + docs/{eng,kor}/*.md 16개 파일에서 Reflex 언급 제거** — `architecture.md`, `quickstart.md`, `development.md`, `troubleshooting.md`, `docker-deployment.md`, `SETUP_GUIDE.md`, `EXECUTION_LOG.md`, `README.md`. 새 Next.js + shadcn 구조 반영.
- [ ] **Auth 흐름 다이어그램 갱신** — 쿠키 기반 + Next 리라이트 프록시 반영.
- [ ] **Supabase 배포 가이드** — `.env.example` 주석으로만 있음. `docs/eng/supabase-deployment.md` 신규.
- [ ] **API reference 업데이트** — `/api/v1/evaluation/drafts/*` 신규 엔드포인트 5개 문서화.

### 7.6 인프라 / CI (P2)
- [ ] **GitHub Actions 워크플로** — backend pytest + frontend `tsc --noEmit` + `next build` + ruff/eslint.
- [ ] **이미지 사이즈 다이어트** — worker 이미지에 `pip install` 시 wheels 캐시. multi-stage build.
- [ ] **헬스체크 인증** — 현재 `/api/v1/health` 가 db/redis/celery 상태를 노출. 외부 접근 가능하면 정보 누출이라 internal 헬스체크 분리 또는 인증 추가.
- [ ] **Nginx config 검토** — `nginx.conf` 가 있으나 새 쿠키 / CORS / X-Request-ID 설정과 일치하는지 확인.

---
각 항목별로 우선순위(P0/P1/P2)와 일정, 담당자를 지정하여 스프린트 계획에 반영하세요.
