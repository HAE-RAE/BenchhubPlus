# 트러블슈팅 가이드

BenchHub Plus 사용 중 자주 발생하는 문제와 해결 방법을 정리했습니다.

## 🚨 설치 관련 이슈
### Docker 컨테이너 시작 실패
- **증상**: `Cannot connect to the Docker daemon`
- **조치**
  1. Docker 서비스 상태 확인
     ```bash
     sudo systemctl status docker
     sudo systemctl start docker
     ```
  2. 권한 추가 후 재로그인
     ```bash
     sudo usermod -aG docker $USER
     ```
  3. 버전 확인: `docker --version`, `docker-compose --version`

### PostgreSQL 연결 실패
- **증상**: `sqlalchemy.exc.OperationalError`
- **조치**
  1. Docker 로그 또는 `systemctl status postgresql` 확인
  2. `psql -h localhost -U benchhub -d benchhub_plus`로 직접 연결 테스트
  3. 방화벽 포트(5432) 허용

### Redis 연결 실패
- **증상**: `redis.exceptions.ConnectionError`
- **조치**
  1. `docker compose logs redis` 또는 `systemctl status redis`
  2. `redis-cli ping` 실행 (결과 `PONG` 확인)
  3. Redis 설정값(`bind`, `port`) 확인

## ⚙️ 런타임 이슈
### API 500 오류
- **로그 확인**: `docker compose logs backend` 또는 `tail -f logs/backend.log`
- **환경 변수 확인**: `docker compose exec backend env | grep DATABASE_URL`
- **DB 연결 테스트**
  ```bash
  docker compose exec backend python -c "from apps.core.db import get_db; next(get_db()); print('OK')"
  ```

### 작업이 PENDING에서 멈춤
- **워커 로그 확인**: `docker compose logs worker`
- **Redis 연결 테스트**
  ```bash
  docker compose exec worker python -c "import redis; print(redis.Redis(host='redis', port=6379, db=0).ping())"
  ```
- **워커 재시작**: `docker compose restart worker`

### 프런트엔드 화면이 표시되지 않음
- **프런트엔드 로그**: `docker compose logs reflex` 또는 `reflex run` 실행 중인 터미널 확인
- **포트 확인**: `lsof -i :3000`, `lsof -i :8002`
- **포트 충돌 해결**: `lsof -ti:3000 | xargs kill -9` 후 재시작
- **브라우저 개발자 도구에서 WebSocket 연결 및 네트워크/콘솔 오류 확인**

### 인증/로그인 실패
- **개발 모드에서 Google 로그인 실패 시**: `.env`에 `DEV_AUTH_BYPASS=true` 설정
- **Reflex 프런트엔드에 환경 변수 전달**: `DEV_AUTH_BYPASS=true API_BASE_URL=http://localhost:8000 reflex run --env dev`
- **백엔드 포트 확인**: 네이티브 실행 시 `8000`, Docker 실행 시 `8001`

### HRET 모듈을 찾을 수 없음
- **증상**: `WARNING: HRET not available: No module named 'llm_eval'`
- **해결**: HRET를 로컬에 클론 후 설치
  ```bash
  git clone https://github.com/HAE-RAE/haerae-evaluation-toolkit.git
  pip install -e ./haerae-evaluation-toolkit
  ```

## 🐢 성능 저하
- 샘플 수를 10~50으로 줄여 테스트 후 점진적으로 늘립니다.
- 모델 API 속도/쿼터를 확인하고 키를 분산 사용합니다.
- Celery 워커 동시 실행 수를 조정합니다.
  ```bash
  celery -A apps.backend.celery_app worker --concurrency=4
  ```
- Redis와 데이터베이스 리소스 사용량을 모니터링하세요.

## 🔄 유지보수/정리

### API로 정리 작업 실행 (관리자)
오래된 작업/샘플/캐시를 비동기(202)로 정리할 수 있습니다.

1. 정리 예약(먼저 `dry_run` 권장)
   ```bash
   curl -X POST http://localhost:8001/api/v1/maintenance/cleanup \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <admin_token>" \
     -d '{"dry_run": true, "resources": ["tasks","samples","cache"], "days_old": 7, "limit": 500, "hard_delete": false}'
   ```
   - 기본 리소스: `tasks`, `samples`, `cache`
   - `dry_run=true`로 영향 범위를 먼저 확인
   - `hard_delete=true`면 캐시를 실제 삭제, 기본은 quarantine 처리

2. 상태/진행률 확인
   ```bash
   curl http://localhost:8001/api/v1/maintenance/cleanup/<task_id> \
     -H "Authorization: Bearer <admin_token>"
   ```
   - `status`: `PENDING | RUNNING | PARTIAL | SUCCESS | FAILED`
   - `progress`: `{current, total, stage, eta_seconds}` 형태로 프로그레스 바 표시 가능
   - 리소스별 `{deleted, skipped, errors, duration_ms}`를 반환

## 추가 도움말
- `logs/` 디렉터리에서 서비스별 로그를 확인합니다.
- Docker Compose 사용 시 `docker compose ps`, `docker compose logs -f <service>`로 상태를 점검합니다.
- 문제가 지속되면 GitHub Issues에 로그와 함께 보고하세요.

## 참고 문서
- [설치 가이드](installation.md)
- [Docker 배포](docker-deployment.md)
- [실행 로그](EXECUTION_LOG.md)
