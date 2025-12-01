# 빠른 시작 가이드

BenchHub Plus를 가장 빠르게 실행하는 방법을 안내합니다. 인프라 경험이 없는 초보자도 따라 할 수 있도록 단계별로 설명되어 있습니다.

---

## 🧭 구성 요소 한눈에 보기

BenchHub Plus는 여러 서비스가 상호 통신하며 동작합니다.

| 구성 요소 | 역할 | 기본 개발 포트 |
|-----------|------|----------------|
| Reflex 프런트엔드 | 평가 생성/결과 열람을 위한 웹 UI | `3000` |
| FastAPI 백엔드 | 평가 계획 생성과 작업 오케스트레이션 | `8001` |
| Celery 워커 | 백그라운드에서 평가 작업 실행 | – |
| PostgreSQL | 평가 계획 및 결과 저장소 | `5433` |
| Redis | Celery 브로커 및 캐시 | `6380` |
| Flower (선택) | Celery 모니터링 대시보드 | `5556` |

Docker Compose가 이 모든 서비스를 자동으로 시작하고 연결해 줍니다.

---

## ✅ 시작 전 준비물

| 항목 | 비고 |
|------|------|
| **운영체제** | macOS, Linux, Windows(WSL2) |
| **Git** | [git-scm.com](https://git-scm.com/downloads)에서 설치 |
| **Docker Desktop/Engine** | Docker Compose v2 포함 |
| **모델 API 키** | OpenAI 혹은 기타 지원 모델 제공자의 API 키 |

> ℹ️ Docker를 사용할 수 없다면 가이드 마지막의 "로컬 Python 환경" 경로를 참고하세요.

---

## 🚀 1단계 – 저장소 클론

```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
```

---

## 🛠️ 2단계 – `.env` 파일 생성 및 편집

1. 예시 파일을 복사합니다.

   ```bash
   cp .env.example .env
   ```

2. 원하는 편집기로 `.env` 파일을 열고 다음 값을 설정합니다.
   - `OPENAI_API_KEY`: 사용할 모델 제공자의 키를 붙여 넣습니다.
   - `POSTGRES_PASSWORD`: 번들 PostgreSQL 데이터베이스에 사용할 강력한 비밀번호를 지정합니다.
   - 포트 충돌이 있다면 관련 환경 변수를 수정합니다.

> 대부분의 기본값은 첫 실행에 적합합니다.

---

## 🧪 3단계 – 스크립트로 전체 스택 실행

길고 복잡한 Docker Compose 명령 대신 헬퍼 스크립트를 사용합니다.

```bash
./scripts/deploy.sh development
```

스크립트는 다음을 자동으로 수행합니다.

1. Docker 및 Docker Compose 설치 여부 확인
2. 백엔드·워커·프런트엔드 이미지를 빌드
3. `docker-compose.dev.yml`을 백그라운드로 실행
4. PostgreSQL, Redis, API, 프런트엔드가 준비될 때까지 대기
5. 데이터베이스 스키마 초기화

첫 실행 시에는 Docker가 베이스 이미지를 내려받느라 몇 분 정도 소요될 수 있습니다.

---

## 🔍 4단계 – 서비스 상태 확인

스크립트 완료 후 요약 메시지와 함께 주요 URL이 출력됩니다. 수동으로 점검하려면 아래 명령을 실행하세요.

```bash
curl http://localhost:8001/api/v1/health
```

- 응답 JSON에 `"status": "healthy"`가 포함되면 백엔드가 정상입니다.
- Flower 대시보드: http://localhost:5556 에 접속해 워커 상태를 확인할 수 있습니다.

---

## 🕹️ 5단계 – 웹 앱 열기

브라우저에서 **http://localhost:3000** 으로 이동합니다. 기본 탭은 **Evaluate**이며, [사용자 매뉴얼](./user-manual.md)에서 각 입력 항목을 자세히 설명합니다.

---

## ⏹️ 중지 및 재시작

```bash
# 개발 스택 중지
docker-compose -f docker-compose.dev.yml down

# 나중에 다시 시작
./scripts/deploy.sh development
```

Docker는 PostgreSQL/Redis 볼륨을 유지하므로 이전 결과가 삭제되지 않습니다.

---

## 🧑‍💻 대안: 로컬 Python 환경

Docker 대신 직접 실행하고 싶다면 다음 절차를 따르세요(Python 3.11+ 필요).

```bash
./scripts/setup.sh      # 가상환경 생성 및 의존성 설치
source venv/bin/activate
```

이후 각 컴포넌트를 별도 터미널에서 실행합니다.

```bash
# 터미널 1 – FastAPI 백엔드
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 터미널 2 – Celery 워커
celery -A apps.worker.celery_app worker --loglevel=info

# 터미널 3 – Reflex 프런트엔드
cd apps/reflex_frontend
API_BASE_URL=http://localhost:8000 reflex run --env dev --backend-host 0.0.0.0 --backend-port 8001 --frontend-host 0.0.0.0 --frontend-port 3000
```

이 방식에서는 `.env`에 정의된 연결 정보에 맞는 PostgreSQL과 Redis 인스턴스를 직접 마련해야 합니다.

---

## 📚 다음 단계

- [사용자 매뉴얼](./user-manual.md)에서 UI 사용법을 익히세요.
- [설치 가이드](./installation.md)로 운영/배포 모범 사례를 학습하세요.
- [API 레퍼런스](./api-reference.md)를 확인해 자동화에 활용하세요.

즐거운 벤치마킹 되세요! 🎉
