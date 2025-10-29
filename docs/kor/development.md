# 개발 가이드

BenchHub Plus 개발 환경 구성과 워크플로우를 정리했습니다.

## 🏗️ 아키텍처 개요
- Streamlit 프런트엔드
- FastAPI 백엔드
- Celery 워커 + Redis 큐
- PostgreSQL/SQLite 데이터베이스
- HRET 통합 계층

## 개발 환경 준비
### 필수 조건
- Python 3.11 이상
- PostgreSQL 12+, Redis 6+
- Git, Docker(선택 사항)

### 빠른 설치
```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
./scripts/setup.sh
cp .env.example .env  # 환경 설정
./scripts/deploy.sh development
```

### 수동 설치
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
createdb benchhub_plus_dev
python -c "from apps.core.db import init_db; init_db()"
./scripts/dev-backend.sh   # FastAPI
./scripts/dev-worker.sh    # Celery
./scripts/dev-frontend.sh  # Streamlit
```

## 📁 주요 디렉터리 구조
```
apps/backend      # FastAPI 라우터, 서비스, 저장소
apps/frontend     # Streamlit 앱 및 컴포넌트
apps/worker       # Celery 설정과 작업 정의
apps/core         # 설정, DB, 모델, 스키마 공통 모듈
apps/planner      # LLM 기반 플래너
scripts/          # 배포 및 개발 스크립트
tests/            # 단위/통합/E2E 테스트
```

## 개발 워크플로우
1. 브랜치 생성: `git checkout -b feature/<이름>`
2. 기능 개발 후 테스트 실행: `./scripts/test.sh` 또는 `pytest`
3. 코드 포맷팅: `black`, `isort`
4. 린팅: `flake8`, `mypy`
5. 커밋/푸시 후 PR 생성

### 코드 스타일 도구
```bash
pip install black isort flake8 mypy pytest
black apps/
isort apps/
flake8 apps/
mypy apps/
pytest tests/
```

### Pre-commit 훅
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## 테스트 전략
```
tests/unit          # 모델, 서비스, 유틸 단위 테스트
tests/integration   # API, 워커, DB 통합 테스트
tests/e2e           # 전체 평가 플로우, 프런트엔드 테스트
tests/fixtures      # 샘플 데이터와 모의 응답
```
- 전체 테스트 실행: `pytest`
- 특정 디렉터리만 실행: `pytest tests/unit`

## 기여 가이드 요약
- Issue 또는 Discussion에서 기능/버그 논의 후 작업 시작
- 커밋 메시지는 `feat:`, `fix:`, `docs:` 등 Conventional Commits 형식을 권장
- 문서 변경 시 영어/한국어 버전을 함께 업데이트하세요.

## 관련 문서
- [시스템 아키텍처](architecture.md)
- [API 레퍼런스](api-reference.md)
- [Docker 배포](docker-deployment.md)
