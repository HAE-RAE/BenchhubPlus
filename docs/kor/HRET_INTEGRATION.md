# BenchhubPlus용 HRET 통합 가이드

## 개요
이 문서는 BenchhubPlus와 HRET(Haerae Evaluation Toolkit)을 연동하여 한국어 평가를 수행하는 방법을 설명합니다.

## 아키텍처 개요
통합은 다음 구성요소로 이루어집니다.
```
apps/backend/routes/hret.py        # HRET API 엔드포인트
apps/worker/hret_runner.py         # 평가 실행기
apps/worker/hret_config.py         # 설정 관리
apps/worker/hret_mapper.py         # 데이터 포맷 매핑
apps/worker/hret_storage.py        # 결과 저장 로직
apps/worker/tasks.py               # Celery 백그라운드 작업
apps/core/db.py                    # 데이터베이스 모델
```

### 주요 특징
- ✅ HRET 평가 툴킷과 완전 통합
- ✅ 7개의 REST API 엔드포인트 제공
- ✅ Celery 기반 비동기 처리
- ✅ 평가 결과 및 리더보드 자동 저장
- ✅ OpenAI, HuggingFace, LiteLLM 등 다중 모델 지원
- ✅ 한국어 벤치마크에 최적화

## 설치 및 준비
1. **HRET 툴킷 설치**
   ```bash
   git clone https://github.com/HAE-RAE/haerae-evaluation-toolkit.git hret
   cd hret
   pip install -e .
   ```
2. **BenchhubPlus 의존성 설치**
   ```bash
   pip install sqlalchemy pydantic-settings python-jose[cryptography] passlib[bcrypt] celery redis
   ```
3. **데이터베이스 초기화**
   ```bash
   cd BenchhubPlus
   python -c "from apps.core.db import init_db; init_db()"
   ```
4. 기본 사용에는 추가 설정이 필요하지 않으며 HRET 사용 가능 여부를 자동으로 감지합니다.

## 핵심 API 엔드포인트
- `GET /hret/status` : HRET 사용 가능 여부 확인
- `GET /hret/config` : 지원 데이터셋/모델/평가 방법 정보
- `POST /hret/validate-plan` : 평가 계획(YAML) 유효성 검사
- `POST /hret/evaluate` : 평가 실행 요청
- `GET /hret/evaluate/{task_id}` : 작업 진행 상태 조회
- `GET /hret/results` : 평가 결과 조회
- `GET /hret/leaderboard` : 리더보드 요약 정보 확인

각 엔드포인트는 JSON 형식으로 응답하며, 요청에는 계획 YAML과 모델 정보가 포함됩니다.

## 사용 예시
1. **계획 검증**
   ```http
   POST /hret/validate-plan
   {
     "plan_yaml": "version: \"1.0\"\nmetadata:\n  name: \"Test Plan\"\n..."
   }
   ```
2. **평가 실행**
   ```http
   POST /hret/evaluate
   {
     "plan_yaml": "version: \"1.0\"\n...",
     "models": [
       {
         "name": "gpt-3.5-turbo",
         "model_type": "openai",
         "api_key": "sk-...",
         "model_name": "gpt-3.5-turbo"
       }
     ],
     "timeout_minutes": 30,
     "store_results": true
   }
   ```
3. **작업 상태 확인**
   ```http
   GET /hret/evaluate/hret_20241027_123456_1234
   ```

## 데이터 흐름
1. 사용자가 자연어 질의를 입력하면 플래너가 BenchHub 구성을 생성합니다.
2. 구성은 HRET YAML 계획으로 변환되어 `/hret/evaluate` 엔드포인트에 전달됩니다.
3. Celery 워커가 HRET 실행기를 통해 평가를 수행합니다.
4. 결과는 데이터베이스에 저장되고 리더보드 캐시로 반영됩니다.

## 테스트
- `/hret/status` 응답이 `hret_available: true`인지 확인합니다.
- 샘플 평가 계획으로 `validate-plan`과 `evaluate`를 호출해 성공 여부를 확인합니다.
- 결과 조회 API가 최신 결과를 반환하는지 확인합니다.

## 트러블슈팅
- **HRET 미설치**: `hret_available`이 `false`이면 HRET 패키지를 다시 설치하세요.
- **모델 인증 실패**: API 키 권한을 점검하고 제한을 확인하세요.
- **작업 실패**: Celery 로그와 `apps/worker/hret_runner.py` 로그를 확인하세요.
- **데이터 저장 오류**: 데이터베이스 연결 설정과 스키마 초기화를 재확인하세요.

## 추가 참고
- BenchHub 구성 방법은 [BenchHub 구성 가이드](BENCHHUB_CONFIG.md)를 참고하세요.
- API 사용 방식은 [API 레퍼런스](api-reference.md)에서 확인할 수 있습니다.
