# BenchHub Plus 실행 로그

이 문서는 BenchHub Plus를 실제로 구축하면서 수행한 단계와 해결했던 문제를 기록한 것입니다.

## 실행 타임라인

### 1단계: 환경 구성
1. `.env` 파일 생성 및 OpenAI API 키, 서비스 포트 설정
2. `pip install -e .`로 백엔드 의존성 설치
3. `pip install -r apps/reflex_frontend/requirements.txt`로 프런트엔드 의존성 설치

### 2단계: 서비스 인프라 준비
1. **Redis 서버 설정**
   - 설치: `sudo apt update && sudo apt install redis-server`
   - 실행: `sudo systemctl start redis-server`
   - 확인: `redis-cli ping` → `PONG`
2. **데이터베이스 초기화**
   - SQLite 테이블 생성 (`leaderboard_cache`, `evaluation_tasks`, `experiment_samples`)
   - 데이터베이스 파일: `./benchhub_plus.db`
3. **로그 디렉터리 생성**
   - `logs/` 폴더 생성

### 3단계: 서비스 구동
1. **백엔드(FastAPI)**
   - 명령어: `python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 --reload`
   - 상태: 8000 포트에서 정상 실행
2. **프런트엔드(Reflex)**
   - 명령어: `cd apps/reflex_frontend && API_BASE_URL=http://localhost:8000 reflex run --env dev --backend-host 0.0.0.0 --backend-port 8001 --frontend-host 0.0.0.0 --frontend-port 3000`
   - 상태: 3000 포트(Reflex 백엔드 8001)에서 UI 확인
3. **Celery 워커**
   - 명령어: `celery -A apps.worker.celery_app worker --loglevel=info --concurrency=4`
   - 상태: 4개 워커 프로세스로 실행

## 발생한 이슈와 해결 방법

### 이슈 1: Reflex 의존성 누락
- **증상**: `ModuleNotFoundError: No module named 'reflex'`
- **해결**: `pip install -r apps/reflex_frontend/requirements.txt`
- **원인**: 프런트엔드 의존성 설치 단계 생략

### 이슈 2: SQLAlchemy 2.0 호환성
- **증상**: `sqlalchemy.exc.ArgumentError: Textual SQL expression should be explicitly declared as text()`
- **해결**: `apps/backend/api/status.py`에서 `connection.execute(text("SELECT 1"))`로 수정
- **원인**: SQLAlchemy 2.0에서 raw SQL은 `text()` 래퍼가 필요

### 이슈 3: 포트 충돌
- **증상**: `OSError: [Errno 98] Address already in use`
- **해결**:
  ```bash
  lsof -ti:8000 | xargs kill -9   # FastAPI 포트 해제
  lsof -ti:3000 | xargs kill -9   # Reflex 프런트엔드 포트 해제
  lsof -ti:8001 | xargs kill -9   # Reflex 백엔드 포트 해제
  ```
- **원인**: 이전 실행 프로세스가 포트를 점유

## 서비스 검증
- **Redis**: `redis-cli ping` → `PONG`
- **데이터베이스**: SQLite 파일 존재 및 스키마 확인
- **백엔드**: `/api/v1/health` 응답 정상
- **프런트엔드**: UI 로딩 확인
- **Celery**: 워커 프로세스 활성화

### 헬스 체크 응답 예시
```json
{
  "status": "healthy",
  "timestamp": "2025-10-29T11:11:10.065955",
  "version": "2.0.0",
  "database_status": "connected",
  "redis_status": "connected"
}
```

## UI 기능 테스트
- **테스트 케이스**: "Compare these models on Korean math problems for high school students"
- **결과**: 질의 정상 접수, UI 힌트(Press Ctrl+Enter to apply) 표시
- **모델 구성**: 기본 2개 모델(OpenAI `gpt-3.5-turbo`) 입력 가능

## 성능 지표
- **기동 시간**: Redis 2초, DB 1초, 백엔드 5초, 프런트엔드 8초, Celery 3초 내외
- **자원 사용량**: 메모리 약 200MB, CPU는 유휴 상태에서 최소, 디스크 약 50MB

## 교훈
1. 의존성은 반드시 `requirements.txt`에 기록합니다.
2. 배포 환경에서는 환경 변수 기반 설정이 안전합니다.
3. SQLAlchemy 2.0 이상에서는 `text()` 사용을 습관화합니다.
4. Redis를 가장 먼저 실행하여 의존 관계를 확보합니다.
5. 포트 설정을 문서화하여 구성 요소 간 충돌을 방지합니다.
