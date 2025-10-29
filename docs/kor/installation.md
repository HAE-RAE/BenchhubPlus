# 설치 가이드

BenchHub Plus를 설치하는 대표적인 방법을 정리했습니다.

## 📋 사전 준비
- 운영 체제: Linux, macOS, Windows(WSL2 권장)
- Python 3.11 이상
- 메모리 4GB 이상(권장 8GB+)
- 저장 공간 2GB 이상
- 인터넷 연결(모델 API 호출용)
- PostgreSQL 12+, Redis 6+
- OpenAI 및 평가 대상 모델의 API 키

## 🚀 빠른 설치 (Docker 권장)
```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
./scripts/setup.sh
cp .env.example .env  # API 키 입력
./scripts/deploy.sh development
```
- 프런트엔드: http://localhost:8502
- 백엔드 API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## 🐳 Docker 상세 설치
1. **Docker & Compose 설치**
   - Ubuntu/Debian: `get.docker.com` 스크립트 사용
   - macOS/Windows: Docker Desktop 설치
2. **저장소 클론 및 스크립트 권한 부여**
   ```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
chmod +x scripts/*.sh
./scripts/setup.sh
```
3. **환경 변수 설정**
   ```bash
cp .env.example .env
nano .env
```
   필수 값:
   ```env
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_PASSWORD=secure_password_here
DEBUG=false
LOG_LEVEL=info
```
4. **배포 실행**
   ```bash
./scripts/deploy.sh development   # 개발용
./scripts/deploy.sh production    # 운영용
```

## 🔧 로컬 개발 설치 (Docker 미사용)
1. **시스템 패키지 설치**
   - Ubuntu: `python3.11`, `postgresql`, `redis`, `libpq-dev` 등 설치
   - macOS: `brew install python@3.11 postgresql redis`
2. **Python 가상환경 구성**
   ```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
```
3. **데이터베이스 준비**
   ```bash
sudo systemctl start postgresql
sudo -u postgres psql
```
   ```sql
CREATE DATABASE benchhub_plus;
CREATE USER benchhub WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE benchhub_plus TO benchhub;
```
   ```bash
sudo systemctl start redis
```
4. **환경 변수 작성**
   ```bash
cp .env.example .env
```
   ```env
DATABASE_URL=postgresql://benchhub:your_password@localhost:5432/benchhub_plus
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_api_key_here
```
5. **데이터베이스 초기화**
   ```bash
python -c "from apps.core.db import init_db; init_db()"
```
6. **서비스 실행**
   ```bash
./scripts/dev-backend.sh   # 백엔드
./scripts/dev-worker.sh    # 워커
./scripts/dev-frontend.sh  # 프런트엔드
```

## 추가 팁
- Windows에서는 WSL2(Ubuntu) 환경을 권장합니다.
- API 키와 비밀 정보는 `.env` 파일에만 보관하고 Git에 커밋하지 마세요.
- 배포 후 `docker compose logs -f`로 로그를 확인하세요.

## 관련 문서
- [설치/설정 가이드](SETUP_GUIDE.md)
- [Docker 배포](docker-deployment.md)
- [빠른 시작](quickstart.md)
