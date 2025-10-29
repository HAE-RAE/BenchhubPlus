# 사용자 매뉴얼

이 문서는 [빠른 시작 가이드](./quickstart.md)를 따라 스택을 실행한 후 BenchHub Plus를 활용하는 방법을 설명합니다. 초보자도 평가를 생성하고 결과를 이해할 수 있도록 실무 중심으로 구성했습니다.

---

## 1. 접속 및 기본 화면

BenchHub Plus는 별도의 계정을 요구하지 않습니다. 서비스가 실행 중이라면 브라우저에서 다음 주소로 이동하세요.

- **개발 환경 (`docker-compose.dev.yml`)**: http://localhost:8502
- **운영 환경 (`docker-compose.yml`)**: http://localhost:8501

상단에는 BenchHub Plus 로고와 함께 **Evaluate**, **Status**, **Browse**, **System** 네 가지 탭이 표시됩니다.

> 💡 페이지가 열리지 않는다면 `docker-compose -f docker-compose.dev.yml ps`로 컨테이너가 실행 중인지 확인하고, 백엔드 헬스 체크(`{"status": "healthy"}`)를 다시 확인하세요.

---

## 2. Evaluate 탭 – 새로운 평가 생성

평가 시작은 항상 Evaluate 탭에서 진행합니다.

### 2.1 평가 설명 입력

- **Natural Language Query** 영역에 평가지 목표를 자연어로 작성합니다.
  - 예시: "한국 고등학교 수학 문제에서 GPT-4와 Claude 3을 비교해줘"
  - 예시: "Python 버그 수정 능력을 평가해줘"
  - 예시: "영어-일본어 번역 품질을 비교해줘"
- 좋은 계획을 얻는 팁
  - 주제(수학, 과학, 코딩 등)를 명시합니다.
  - 필요한 경우 언어와 난이도를 함께 적습니다.
  - QA, 추론, 생성 등 원하는 작업 유형을 기재합니다.

### 2.2 모델 설정

BenchHub Plus는 여러 모델을 동시에 평가할 수 있습니다. 각 모델 카드에는 다음 항목이 포함됩니다.

| 항목 | 설명 |
|------|------|
| **Model Name** | 리더보드에 표시될 이름 (예: `gpt-4`, `claude-3`) |
| **API Base URL** | 제공자의 엔드포인트 (`https://api.openai.com/v1`, `https://api.anthropic.com` 등) |
| **API Key** | 제공자의 비밀 토큰. 세션 동안 메모리에만 저장됩니다. |
| **Model Type** | `openai`, `anthropic`, `huggingface`, `custom` 중 선택 (백엔드 처리 방식 결정) |

추가 안내:

- 상단의 **Number of models to evaluate** 컨트롤로 모델 수를 최대 10개까지 늘릴 수 있습니다.
- API 키 입력란은 비밀번호 형태로 표시되어 안전하게 입력할 수 있습니다.
- 제출 전 각 모델에 이름·Base URL·키가 모두 채워졌는지 검증합니다.

> 🔐 보안 팁: 프런트엔드는 API 키를 디스크에 저장하지 않습니다. 세션을 마치면 브라우저를 닫아 키를 메모리에서 제거하세요.

### 2.3 평가 제출

1. 질의와 모델 정보를 다시 확인합니다.
2. **🚀 Start Evaluation** 버튼을 클릭합니다.
3. 요청이 `/api/v1/leaderboard/generate`로 전송되는 동안 스피너가 표시됩니다.
4. 성공하면 녹색 알림과 함께 **Task ID**가 표시되고, 자동으로 **Status** 탭으로 이동합니다.

필수 입력이 비어 있거나 API 오류가 발생하면 빨간색 오류 메시지로 안내합니다.

---

## 3. Status 탭 – 실시간 진행 상황 추적

Status 탭은 현재 작업 패널과 최근 작업 기록으로 구성됩니다.

### 3.1 현재 작업 패널

- **Task ID**와 **Refresh Status** 버튼이 표시됩니다.
- `/api/v1/tasks/<task_id>` 엔드포인트에서 실시간 데이터를 받아옵니다.
- 상태는 이모지와 함께 나타납니다.
  - 🟡 `PENDING` – 대기 중입니다.
  - 🔵 `STARTED` – 워커에서 실행 중 (5초마다 자동 새로고침).
  - 🟢 `SUCCESS` – 완료되어 결과가 준비되었습니다.
  - 🔴 `FAILURE` – 오류가 발생했습니다. 메시지를 확인하세요.
- 작업이 완료되면 아래 결과 영역이 자동으로 렌더링됩니다.
- **Task Details**를 펼치면 백엔드가 반환한 원본 JSON을 확인할 수 있습니다.

### 3.2 작업 기록 테이블

- 브라우저 세션에서 제출한 최근 10개 작업을 나열합니다.
- `Task ID`, `Query`, `Models`, `Submitted`, `Status` 열로 구성됩니다.
- 이전 결과를 다시 열람할 때 유용합니다.

---

## 4. 결과 해석하기

작업이 성공하면 Status 탭 하단에 상세 결과 대시보드가 표시됩니다.

### 4.1 리더보드 테이블

- 백엔드가 반환한 `Score` 기준으로 모델 순위를 표시합니다.
- `Accuracy`, `Samples`, `Execution Time` 등의 추가 열이 포함됩니다.
- 색상 그라데이션으로 상위 모델을 직관적으로 확인할 수 있습니다.

### 4.2 시각화 비교

- **막대 차트**: 모델별 Score를 비교합니다.
- **레이더 차트**: Score, Accuracy, 샘플 수를 한눈에 보여줍니다(2개 이상 모델일 때 표시).

### 4.3 상세 JSON

**Detailed Results** 섹션을 펼치면 전체 JSON 응답을 볼 수 있습니다. 원시 데이터를 내보내거나 통합을 디버깅할 때 활용하세요.

> 💾 결과를 저장하려면 JSON 블록 옆 복사 버튼을 사용하거나 `/api/v1/tasks/<task_id>`에서 직접 다운로드하세요.

---

## 5. Browse 탭 – 과거 리더보드 탐색

Browse 탭은 `/api/v1/leaderboard/browse` 엔드포인트를 사용합니다.

1. **Language**, **Subject**, **Task Type**, **Max Results** 필터를 선택합니다.
2. **🔍 Search Leaderboard** 버튼을 클릭합니다.
3. 순위, 모델명, 점수, 메타데이터, 업데이트 시각이 포함된 테이블을 확인합니다.
4. 상위 10개 모델을 보여주는 가로 막대 차트로 빠르게 비교할 수 있습니다.

필터에 맞는 데이터가 없으면 안내 메시지가 표시됩니다.

---

## 6. System 탭 – 헬스 체크 및 용량 모니터링

시스템 이상이 의심될 때 활용하세요.

- `/api/v1/health` 응답 요약
  - 데이터베이스와 Redis 연결 상태
  - API 가용성 상태
- `/api/v1/stats` 실시간 지표
  - 대기/실행/완료/실패 작업 수
  - 캐시된 리더보드 엔트리 수
  - 플래너 에이전트 사용 가능 여부

특정 컴포넌트가 비정상이라면 `docker-compose -f docker-compose.dev.yml logs <서비스>` 명령으로 로그를 확인하거나 배포 스크립트를 재실행하세요.

---

## 7. 트러블슈팅 요약표

| 증상 | 권장 조치 |
|------|-----------|
| **Evaluate 탭에 API 오류 표시** | API 키 유효성과 쿼터를 확인하고, 백엔드 로그에서 제공자별 오류를 확인합니다. |
| **작업이 PENDING에서 멈춤** | 워커 컨테이너가 실행 중인지 `docker ps`로 확인하고 `docker-compose -f docker-compose.dev.yml restart worker`로 재시작합니다. |
| **작업이 즉시 실패** | Task Details의 오류 메시지를 확인하세요. API Base URL 오타, 지원되지 않는 모델 유형, 제공자 장애가 흔한 원인입니다. |
| **프런트엔드가 백엔드에 연결하지 못함** | `API_BASE_URL`이 노출한 백엔드 포트(기본 `http://localhost:8001`)와 일치하는지 확인합니다. |
| **지표가 비어 보임** | 샘플 수가 적을 수 있습니다. 샘플 수를 늘리거나 평가 계획이 정상적으로 질문을 생성했는지 점검하세요. |

---

## 8. 데이터 및 로그 위치

- **Docker 볼륨**: PostgreSQL과 Redis 데이터는 `postgres_dev_data`, `redis_dev_data` 볼륨에 저장됩니다.
- **애플리케이션 로그**: 저장소의 `logs/` 디렉터리에 마운트됩니다.
- **임시 파일**: 워커 컨테이너 내부의 `/tmp` 경로를 사용합니다.

정리하려면 다음 명령을 실행하세요.

```bash
docker-compose -f docker-compose.dev.yml down -v   # 컨테이너와 볼륨 삭제
rm -rf logs/*                                      # 애플리케이션 로그 정리
```

---

## 9. 프로그램 연동 방법

UI가 수행하는 모든 작업은 REST API로도 접근할 수 있습니다. 자주 사용하는 엔드포인트는 다음과 같습니다.

| 엔드포인트 | 설명 |
|------------|------|
| `POST /api/v1/leaderboard/generate` | UI와 동일한 페이로드로 평가를 제출합니다. |
| `GET /api/v1/tasks/<task_id>` | 작업 진행 상황을 폴링하고 결과를 가져옵니다. |
| `GET /api/v1/leaderboard/browse` | 과거 리더보드 엔트리를 조회합니다. |
| `GET /api/v1/health` | 서비스 헬스 체크( System 탭에서 사용 ). |

세부 요청/응답 스키마는 [API 레퍼런스](./api-reference.md)를 참고하세요.

---

## 10. 추가 지원

- **문서**: 빠른 시작, 설치 가이드, API 레퍼런스, 본 매뉴얼이 대부분의 워크플로를 다룹니다.
- **GitHub Issues**: https://github.com/HAE-RAE/BenchhubPlus/issues 에서 버그 신고나 기능 제안을 남기세요.
- **Discussions**: 커뮤니티와 사용 경험을 공유하거나 질문을 남기세요.
- **기업 지원**: 맞춤 통합 또는 교육이 필요하다면 BenchHub Plus 관리자에게 문의하세요.

즐거운 벤치마킹 되세요! 🎉
