# BenchHub Plus 실행 로그

이 문서는 BenchHub Plus를 실제로 구축하면서 수행한 단계와 해결했던 문제를 기록한 것입니다.

## 실행 타임라인

### 1단계: 환경 구성
1. `.env` 파일 생성 및 OpenAI API 키, 서비스 포트 설정
2. `requirements.txt`를 이용한 기본 의존성 설치
3. `streamlit-option-menu` 추가 설치

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
   - 명령어: `python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 12000 --reload`
   - 상태: 12000 포트에서 정상 실행
2. **프런트엔드(Streamlit)**
   - 명령어: `streamlit run apps/frontend/streamlit_app.py --server.port 12001 --server.address 0.0.0.0`
   - 상태: 12001 포트에서 UI 확인
3. **Celery 워커**
   - 명령어: `celery -A apps.backend.celery_app worker --loglevel=info --concurrency=4`
   - 상태: 4개 워커 프로세스로 실행

## 발생한 이슈와 해결 방법

### 이슈 1: `streamlit-option-menu` 누락
- **증상**: `ModuleNotFoundError: No module named 'streamlit_option_menu'`
- **해결**: `pip install streamlit-option-menu`
- **원인**: requirements.txt에 패키지가 누락됨

### 이슈 2: `os` 모듈 미임포트
- **증상**: `NameError: name 'os' is not defined`
- **해결**: `apps/frontend/streamlit_app.py`에 `import os` 추가
- **원인**: `os.getenv()` 사용 중 임포트 누락

### 이슈 3: SQLAlchemy 2.0 호환성
- **증상**: `sqlalchemy.exc.ArgumentError: Textual SQL expression should be explicitly declared as text()`
- **해결**: `apps/backend/api/status.py`에서 `connection.execute(text("SELECT 1"))`로 수정
- **원인**: SQLAlchemy 2.0에서 raw SQL은 `text()` 래퍼가 필요

### 이슈 4: Streamlit Secrets 설정
- **증상**: `FileNotFoundError: .streamlit/secrets.toml`
- **해결**: Secrets 대신 환경 변수(`os.getenv`) 사용
- **원인**: `secrets.toml` 미구성 환경에서 실행

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

## 향후 권장 사항
1. 전체 설치를 자동화하는 `setup.sh` 스크립트 유지
2. Docker Compose 기반 컨테이너 배포 검토
3. 헬스 체크 및 모니터링 고도화
4. 통합 로그 정책 수립
5. 오류 메시지 및 복구 전략 개선

## 다음 단계
- 모델 평가 요청 실행
- BenchHub 구성 검증 테스트
- 플래너 에이전트 통합 테스트
- HRET 평가 워크플로우 검증
