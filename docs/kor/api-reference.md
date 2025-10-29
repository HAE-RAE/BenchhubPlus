# API 레퍼런스

BenchHub Plus REST API의 핵심 엔드포인트와 요청/응답 형식을 정리합니다.

## 🌐 기본 URL
- **개발 환경**: `http://localhost:8000`
- **운영 환경**: `https://your-domain.com`

모든 엔드포인트는 `/api/v1` 경로를 접두사로 사용합니다.

## 🔐 인증
외부 모델 서비스 호출 시 Bearer 토큰 방식의 API 키 인증을 사용합니다.
```http
Authorization: Bearer your-api-key
```

## 📋 주요 엔드포인트

### 헬스 체크
- **GET `/api/v1/health`** : 시스템 상태 확인
  - 응답 예시
    ```json
    {
      "status": "healthy",
      "database_status": "connected",
      "redis_status": "connected",
      "planner_available": true,
      "timestamp": "2024-01-15T10:30:00Z"
    }
    ```
  - 상태 코드: `200` 정상, `503` 문제 발생

### 리더보드 관리
- **POST `/api/v1/leaderboard/generate`** : 자연어 질의 기반 리더보드 생성
  - 요청 본문에는 질의, 모델 목록, 평가 기준을 포함합니다.
  - 성공 시 작업 ID와 예상 소요 시간이 반환됩니다.
- **GET `/api/v1/leaderboard/browse`** : 기존 리더보드 조회
  - 언어, 주제, 과업, 점수 범위 등 다양한 필터와 정렬 옵션 제공

### 작업 관리
- **GET `/api/v1/tasks/{task_id}`** : 작업 상세 정보 조회
  - 진행률, 결과, 모델별 지표, 실행 시간 확인
- **DELETE `/api/v1/tasks/{task_id}`** : 완료된 작업 삭제

### 평가 계획 및 샘플
- **POST `/api/v1/planner/plan`** : 자연어 질의를 BenchHub 계획으로 변환
- **POST `/api/v1/planner/preview`** : 계획 미리보기 및 샘플 추출
- **GET `/api/v1/samples/{task_id}`** : 평가 샘플 데이터를 조회

### 벤치마크 메타데이터
- **GET `/api/v1/benchmarks/subjects`** : BenchHub 주제 목록 반환
- **GET `/api/v1/benchmarks/tasks`** : 과업 유형 목록 반환

## 요청 및 응답 형식
- 대부분의 엔드포인트는 JSON 요청/응답을 사용합니다.
- 대량 데이터 조회 시 `limit`, `offset` 파라미터로 페이지네이션이 가능합니다.
- 오류 응답은 다음 형식을 따릅니다.
  ```json
  {
    "detail": "Validation error",
    "errors": [
      {"loc": ["body", "query"], "msg": "field required", "type": "value_error.missing"}
    ]
  }
  ```

## 상태 코드 요약
- `200` 성공
- `201` 리소스 생성
- `400` 잘못된 요청
- `401` 인증 실패
- `404` 리소스를 찾을 수 없음
- `422` 유효성 검사 오류
- `500` 서버 내부 오류

## 모범 사용 사례
1. **헬스 체크 후 작업 생성**: `/health`로 상태 확인 후 `/leaderboard/generate` 호출
2. **작업 진행 모니터링**: 반환된 `task_id`로 `/tasks/{task_id}`를 주기적으로 확인
3. **결과 활용**: `/leaderboard/browse` 또는 `/samples/{task_id}`로 세부 결과 조회

## 참고 자료
- [BenchHub 구성 가이드](BENCHHUB_CONFIG.md)
- [HRET 통합 가이드](HRET_INTEGRATION.md)
- [사용자 매뉴얼](user-manual.md)
