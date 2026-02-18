# Docker 배포 가이드

Docker와 Docker Compose를 사용해 BenchHub Plus를 배포하는 방법을 설명합니다.

## 🐳 개요
필수 컨테이너
- **frontend**: Reflex UI
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
- 프런트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8001
- API 문서: http://localhost:8001/docs

### 운영 환경
```bash
./scripts/deploy.sh production
```
- 애플리케이션: http://localhost (또는 http://localhost:3000 직접 접근)
- API: http://localhost/api
- 헬스 체크: http://localhost/api/v1/health

## 🔧 환경 변수
`.env` 파일에 다음 값을 설정합니다.
```env
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=32바이트_이상의_난수_시크릿
CORS_ALLOWED_ORIGINS=https://frontend.example.com
POSTGRES_PASSWORD=secure_database_password
POSTGRES_USER=benchhub
POSTGRES_DB=benchhub_plus
REDIS_URL=redis://redis:6379/0
DEBUG=false
LOG_LEVEL=info
DOMAIN=your-domain.com
SSL_EMAIL=your-email@domain.com
```

### 시크릿 로테이션 절차

1. **새로운 값 준비**: 보안 저장소에서 새로운 `SECRET_KEY`와 외부 API 키를 생성합니다.
2. **환경 변수 갱신**: Kubernetes Secret, Docker Compose `.env` 등 배포 환경에 최신 값을 반영합니다.
3. **서비스 재시작**: 백엔드와 Celery 워커를 재기동해 암호화 키와 API 자격 증명을 다시 불러옵니다.
4. **정상 여부 확인**: `GET /api/v1/health` 엔드포인트를 호출해 데이터베이스, Redis, Celery 상태가 `connected`인지 확인합니다.

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

## 🗄️ 데이터베이스 시딩

BenchHub Plus는 사전 집계된 벤치마크 데이터를 Parquet 파일로부터 자동으로 로드하는 시딩 시스템을 사용합니다.

### 시드 데이터 요구사항

**중요**: 배포 전에 저장소 루트에 `seeds/seed_data.parquet` 파일이 존재해야 합니다. 이 파일은 사전 집계된 평가 결과를 포함하며 컨테이너 시작 시 자동으로 로드됩니다.

#### 시드 파일 스키마

Parquet 파일은 다음 컬럼들을 포함해야 합니다:

| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `model_name` | string | 모델 고유 식별자 | "Qwen_Qwen2.5-72B-Instruct" |
| `language` | string | 평가 언어 | "Korean", "English" |
| `subject_type` | string | 주제 카테고리 | "HASS/Economics", "Tech./Coding" |
| `task_type` | string | 과업 유형 | "Knowledge", "Reasoning" |
| `score` | float64 | 성능 점수 (0.0-1.0) | 0.852 |

#### 시딩 과정

1. **시작 시 확인**: 백엔드 컨테이너 시작 시 LeaderboardCache 테이블이 비어있는지 확인
2. **자동 시딩**: 비어있으면 `seeds/seed_data.parquet`를 읽어 데이터베이스 채움
3. **멱등성 보장**: 데이터가 이미 존재하면 중복 방지를 위해 시딩 건너뜀
4. **로깅**: 모든 시딩 작업이 모니터링을 위해 로그에 기록됨

#### 예상 로그 메시지

**첫 배포 (빈 데이터베이스):**
```
INFO:apps.backend.seeding:Database is empty. Seeding initial data from 'data/seed_data.parquet'...
INFO:apps.backend.seeding:Database seeding complete. Added 4528 records.
```

**재배포 (기존 데이터 존재):**
```
INFO:apps.backend.seeding:LeaderboardCache already contains data. Skipping seeding.
```

#### 시드 파일 누락 시

시드 파일이 없으면 애플리케이션은 정상 시작되지만 빈 리더보드로 시작됩니다:

```
WARNING:apps.backend.seeding:Seed file not found at 'data/seed_data.parquet'. Skipping.
```

### 시딩 문제 해결

**문제**: 시딩 오류로 컨테이너 시작 실패  
**해결**: `seeds/seed_data.parquet` 파일 존재 여부와 올바른 스키마 확인

**문제**: 재시작 후 데이터 중복  
**해결**: 멱등성 검사로 인해 발생하지 않아야 함. 발생 시 LeaderboardRepository.get_leaderboard() 메서드 확인

**문제**: 시딩 시간이 너무 오래 걸림  
**해결**: 시드 파일 크기 최적화 또는 대량 삽입 작업 구현 고려

## 추가 참고 문서
- [설치 가이드](SETUP_GUIDE.md)
- [트러블슈팅](troubleshooting.md)
- [개발 가이드](development.md)
