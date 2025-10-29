# Docker 배포 가이드

Docker와 Docker Compose를 사용해 BenchHub Plus를 배포하는 방법을 설명합니다.

## 🐳 개요
필수 컨테이너
- **frontend**: Streamlit UI
- **backend**: FastAPI API
- **worker**: Celery 작업 처리기
- **postgres**: 데이터베이스
- **redis**: 캐시 및 큐
- **nginx**: 프로덕션 역방향 프록시(선택)

## 📋 사전 준비
- Docker 20.10 이상
- Docker Compose 2.0 이상
- 메모리 4GB+, 저장 공간 10GB+
- 모델 API 호출을 위한 인터넷 연결

### 설치 예시
- **Ubuntu/Debian**
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  sudo usermod -aG docker $USER
  ```
- **macOS/Windows**: Docker Desktop 설치

## 🚀 빠른 배포
### 개발 환경
```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
./scripts/setup.sh
cp .env.example .env  # 환경 변수 입력
./scripts/deploy.sh development
```
- 프런트엔드: http://localhost:8502
- 백엔드 API: http://localhost:8001
- API 문서: http://localhost:8001/docs

### 운영 환경
```bash
./scripts/deploy.sh production
```
- 애플리케이션: http://localhost
- API: http://localhost/api
- 헬스 체크: http://localhost/api/v1/health

## 🔧 환경 변수
`.env` 파일에 다음 값을 설정합니다.
```env
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_PASSWORD=secure_database_password
POSTGRES_USER=benchhub
POSTGRES_DB=benchhub_plus
REDIS_URL=redis://redis:6379/0
DEBUG=false
LOG_LEVEL=info
DOMAIN=your-domain.com
SSL_EMAIL=your-email@domain.com
```

## 🧱 Docker Compose 파일
- `docker-compose.dev.yml`: 개발용. 포트 매핑, 라이브 리로드, 볼륨 공유 지원
- `docker-compose.yml`: 운영용. Nginx, Certbot(옵션), 자동 재시작 정책 적용

## 📦 컨테이너 관리 명령어
```bash
docker compose -f docker-compose.dev.yml up -d      # 개발 환경 시작
docker compose -f docker-compose.dev.yml down       # 개발 환경 종료
docker compose logs -f backend                      # 백엔드 로그 확인
docker compose exec postgres psql -U benchhub       # DB 접속
```

## 모니터링 및 유지보수
- 로그 파일은 `docker compose logs -f <service>`로 확인
- 백업은 PostgreSQL 볼륨(`postgres_data`)과 `logs/` 디렉터리를 주기적으로 저장
- 운영 환경에서는 HTTPS 구성을 위해 `DOMAIN`, `SSL_EMAIL` 값을 설정하고 Certbot을 실행하세요.

## 문제 해결
- **컨테이너가 종료될 때**: `docker compose ps`로 상태 확인 후 `logs` 점검
- **포트 충돌**: `.env` 또는 Compose 파일의 포트 값을 조정
- **모델 API 오류**: API 키가 올바른지 확인하고 네트워크 정책을 점검
- **데이터베이스 초기화 실패**: `init.sql` 매핑 여부와 권한 설정을 확인

## 추가 참고 문서
- [설치 가이드](SETUP_GUIDE.md)
- [트러블슈팅](troubleshooting.md)
- [개발 가이드](development.md)
