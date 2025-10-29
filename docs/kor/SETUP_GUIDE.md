# BenchHub Plus 설치 가이드

이 문서는 BenchHub Plus를 설치하고 실행하는 전체 절차를 단계별로 설명합니다.

## 사전 준비
- Python 3.8 이상
- Git
- OpenAI API 키 또는 기타 LLM 제공자 API 키

## 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
```

### 2. 환경 변수 파일 작성
루트 디렉터리에 `.env` 파일을 생성하고 다음 값을 채웁니다.
```env
# API 설정
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-3.5-turbo

# 서비스 포트
API_BASE_URL=http://localhost:12000
FRONTEND_PORT=12001
BACKEND_PORT=12000
REDIS_PORT=6379

# 데이터베이스
DATABASE_URL=sqlite:///./benchhub_plus.db

# Celery 설정
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
pip install streamlit-option-menu
```

### 4. Redis 서버 설치 및 실행
- **Ubuntu/Debian**
  ```bash
  sudo apt update
  sudo apt install redis-server
  sudo systemctl start redis-server
  sudo systemctl enable redis-server
  ```
- **macOS**
  ```bash
  brew install redis
  brew services start redis
  ```
- **Windows**: 공식 배포판 설치 또는 WSL 사용

Redis 실행 확인:
```bash
redis-cli ping
# 결과: PONG
```

### 5. 데이터베이스 초기화
```bash
python -c "from apps.backend.database import engine, Base; from apps.backend.models import *; Base.metadata.create_all(bind=engine)"
mkdir -p logs
```

### 6. 서비스 실행
터미널을 세 개 열어 각각 다음 명령을 실행합니다.

1. **백엔드 (FastAPI)**
   ```bash
   python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 12000 --reload
   ```
2. **프런트엔드 (Streamlit)**
   ```bash
   streamlit run apps/frontend/streamlit_app.py --server.port 12001 --server.address 0.0.0.0
   ```
3. **Celery 워커**
   ```bash
   celery -A apps.backend.celery_app worker --loglevel=info --concurrency=4
   ```

### 7. 설치 확인
- **백엔드 헬스 체크**
  ```bash
  curl http://localhost:12000/api/v1/health
  ```
- **프런트엔드 접속**: http://localhost:12001
- **Redis 상태**
  ```bash
  redis-cli ping
  ```

## 서비스 구조
BenchHub Plus는 다음 네 가지 핵심 구성요소로 이루어져 있습니다.

1. **백엔드 API (FastAPI)** - 포트 12000
   - API 요청 처리
   - 데이터베이스 작업 수행
   - 평가 작업 오케스트레이션

2. **프런트엔드 UI (Streamlit)** - 포트 12001
   - 평가 요청 입력
   - 실시간 상태 모니터링
   - 결과 시각화 제공

3. **작업 큐 (Celery + Redis)** - 포트 6379
   - 비동기 작업 처리
   - 평가 작업 관리

4. **데이터베이스 (SQLite)**
   - 평가 결과 저장
   - 리더보드 캐시 관리
   - 샘플 데이터 기록

## 추가 팁
- 개발 환경에서는 `.env` 파일을 통한 설정이 가장 편리합니다.
- 프로덕션 환경에서는 Docker 또는 Kubernetes 배포를 고려하세요.
- `logs/` 디렉터리에 서비스 로그를 저장하여 문제를 추적하세요.

## 문제 해결
- 포트 충돌이 발생하면 `.env` 파일의 포트 값을 변경하세요.
- Redis가 실행되지 않으면 `redis-cli ping` 결과를 확인하고 서비스 상태를 재검토하세요.
- 데이터베이스 초기화 오류가 발생하면 `apps/backend/models.py` 경로를 다시 확인하세요.

## 다음 단계
- [빠른 시작 가이드](quickstart.md)
- [사용자 매뉴얼](user-manual.md)
- [Docker 배포 가이드](docker-deployment.md)
