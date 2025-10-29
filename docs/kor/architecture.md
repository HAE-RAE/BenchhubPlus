# 시스템 아키텍처

BenchHub Plus의 전체 구조와 주요 컴포넌트를 요약합니다.

## 🏗️ 상위 구조
```
Streamlit 프런트엔드 ⇄ FastAPI 백엔드 ⇄ Celery 워커
                │                  │
                ▼                  ▼
           PostgreSQL DB        Redis 캐시
                   │
             HRET 통합 계층
```

## 주요 계층

### 프런트엔드 (Streamlit)
- 파일: `apps/frontend/streamlit_app.py`, `components/`
- 역할: 사용자 입력 수집, 상태 시각화, API 호출
- 기술: Streamlit, Plotly, Requests

### 백엔드 (FastAPI)
- 파일: `apps/backend/main.py`, `routers/`, `services/`, `repositories/`
- 패턴: Router → Service → Repository 계층 분리
- 역할: REST API 제공, 비즈니스 로직, DB 작업, 작업 큐 트리거

### 워커 (Celery)
- 파일: `apps/backend/celery_app.py`, `apps/worker/tasks.py`, `apps/worker/hret_runner.py`
- 역할: 비동기 평가 실행, 모델 API 호출, 결과 집계
- 작업 유형: 평가, 데이터 처리, 캐시 관리, 정리 작업

### 데이터 계층
- **PostgreSQL/SQLite**: `leaderboard_cache`, `evaluation_tasks`, `experiment_samples` 테이블과 주요 인덱스
- **Redis**: Celery 큐, 임시 결과 캐시, 세션 데이터, 속도 제한

## 🔄 데이터 흐름
1. 사용자 질의 입력 → 프런트엔드 → 백엔드
2. 플래너가 BenchHub 계획 생성
3. DB에 작업 기록 후 Celery 큐에 작업 등록
4. 워커가 HRET을 통해 평가 수행 및 결과 저장
5. Redis 캐시 업데이트 후 프런트엔드에서 실시간 조회

## 🧠 AI/ML 구성
- **플래너 에이전트**: 자연어 질의를 구조화된 평가 계획으로 변환
- **LLM 실행기**: OpenAI, HuggingFace, LiteLLM 등을 통해 모델 호출
- **평가 메트릭**: 정확도, F1, LLM 판정 등 복합 지표 지원

## 확장 고려 사항
- 서비스 간 통신은 REST API 기반이며, 추가 서비스 연동을 위해 gRPC 또는 메시지 큐를 도입할 수 있습니다.
- 데이터베이스는 PostgreSQL을 기본으로 설계되었으나, 소규모 환경에서는 SQLite로도 실행할 수 있습니다.
- Redis는 필수 컴포넌트이므로 장애 조치 구성을 권장합니다.

## 모니터링 및 로깅
- 각 서비스는 `logs/` 디렉터리에 로그를 남길 수 있도록 설정합니다.
- Celery 워커와 FastAPI는 Prometheus 또는 Grafana와 연동하여 메트릭을 수집할 수 있습니다.

## 보안 권장 사항
- API 엔드포인트는 인증 토큰 기반으로 보호하고, HTTPS 배포를 기본으로 합니다.
- 환경 변수(`.env`)에 비밀 정보를 저장하고 버전 관리에서 제외합니다.
- Docker 배포 시 비밀 정보는 Docker secrets 또는 Kubernetes secrets로 관리하세요.

## 추가 참고
- [개발 가이드](development.md)
- [Docker 배포](docker-deployment.md)
- [BenchHub 구성 가이드](BENCHHUB_CONFIG.md)
