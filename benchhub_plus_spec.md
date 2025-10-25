# BenchHub Plus: Interactive Leaderboard System — Technical Specification (v2.0)

**Version:** 2.0 (Final)  
**Last Updated:** 2025-10-25  
**Authors:** Hanwool Lee, Gemini (AI Assistant)

---

## 1. 프로젝트 비전 (Vision)

"어떤 LLM이 가장 뛰어난가?"라는 질문은 맥락이 없으면 의미가 없다. **BenchHub Plus**는 정적인 리더보드의 한계를 넘어, 사용자의 **자연어 질의와 목적**에 따라 **맞춤형 LLM 순위를 실시간으로 생성**하는 **동적 평가 플랫폼**이다.

핵심 목표:
- 도메인, 언어, 과제 유형 등 다차원 기준에 맞는 개인화 리더보드 제공
- 사전 캐시 + 실시간 평가 결합 (Cache-First, Fallback-to-Live)
- 사용자의 모델(API endpoint)을 직접 평가하는 오픈 플랫폼

---

## 2. 기술 기반 (Foundation)

### 2.1 BenchHub
- 30만+ 질문을 Skill/Subject/Target 기준으로 재분류한 통합 벤치마크 데이터셋.
- 사용자가 지정한 조합(예: `Technology/Programming + Korean`)에 맞게 평가 세트를 즉시 생성.

### 2.2 HRET (Haerae Evaluation Toolkit)
- 다양한 LLM 백엔드(OpenAI, vLLM, LiteLLM 등)에서 평가 실행 가능.
- BenchHub와 연동하여 plan.yaml 기반으로 자동 평가 수행.
- LLM-as-Judge, string_match, math_verify 등 다양한 평가 방식 지원.

---

## 3. 시스템 아키텍처 (System Architecture)

BenchHub Plus는 전 구성요소가 Python 기반으로 작성된 **마이크로서비스 아키텍처**다. 모든 요청은 FastAPI 백엔드로 유입되며, 캐시 Hit 시 즉시 반환, Miss 시 Celery/Redis 기반 비동기 평가로 처리된다.

```mermaid
flowchart LR
  subgraph Client[User]
    UQ[자연어 쿼리<br/>모델정보 입력]
  end

  subgraph FE[Frontend (Streamlit)]
    FE1[폼 입력<br/>모델명·API Base·API Key]
    FE2[generate-leaderboard 요청]
    FE3[task 상태 폴링]
    FE4[리더보드 렌더링]
  end

  subgraph BE[Backend (FastAPI)]
    BE1[POST_generate_leaderboard]
    BE2[유효성검증·보안처리]
    BE3[PlannerAgent 호출]
    BE4[Evaluation Orchestrator]
    BE5[GET_status_task]
  end

  subgraph Planner[Planner Agent (LLM)]
    PL1[자연어 → plan.yaml 변환]
  end

  subgraph DS[Data Store (SQLite/PostgreSQL)]
    DB1[(leaderboard_cache)]
    DB2[(evaluation_tasks)]
    DB3[(experiment_samples)]
  end

  subgraph Queue[Task Queue]
    R[(Redis)]
    C[Celery]
  end

  subgraph Worker[Worker (Celery)]
    W1[HRET run_from_config]
    W2[외부 모델 API 호출]
    W3[결과 집계·저장]
  end

  UQ-->FE1-->FE2-->BE1
  BE1-->BE2-->BE3-->PL1-->BE4
  BE4--캐시조회-->DB1
  DB1--Hit-->BE4-->BE5-->FE3-->FE4
  DB1--Miss-->BE4--작업등록-->C-->R
  C-->W1-->W2-->W3-->DB2
  W3--업데이트-->DB1
  FE3--상태조회-->BE5-->DB2
  DB2--결과반환-->BE5-->FE4
```

---

## 4. 데이터 및 작업 흐름 (I/O Pipeline)

입력 → **(1) 자연어 쿼리, (2) 모델 정보(OpenAI 호환)**  
출력 → **맞춤형 리더보드(JSON + 시각화)**

1. 사용자가 Streamlit UI에 쿼리와 모델 정보를 입력.
2. FastAPI가 요청을 수신, 입력 검증 후 Planner Agent 호출.
3. Planner Agent는 `plan.yaml` 초안을 생성하여 HRET 구조에 맞게 구성.
4. Backend가 leaderboard_cache를 조회. 캐시 Hit 시 1초 이내 응답.
5. Cache Miss 시, 모델 정보를 동적으로 plan.yaml에 주입하고 Celery로 작업 등록.
6. Worker가 HRET을 호출해 외부 API 모델을 평가하고 correctness, 통계, timestamp 등을 저장.
7. DB 업데이트 후 `evaluation_tasks`의 상태가 `SUCCESS`로 바뀌면 프런트엔드에서 결과 리더보드 렌더링.

---

## 5. 핵심 컴포넌트 (Components)

| Component | Language/Framework | 주요 라이브러리 | 역할 |
|------------|--------------------|------------------|------|
| Frontend | Streamlit | streamlit, requests | 사용자 입력/결과 표시, 백엔드 상태 폴링 |
| Backend | FastAPI | fastapi, uvicorn, celery | API, 오케스트레이션, Planner/Evaluator 연계 |
| Planner Agent | Python (LLM SDK) | openai or litellm | 자연어 쿼리를 HRET plan으로 변환 |
| Evaluation Engine | Python (HRET) | haerae-evaluation-toolkit | 캐시조회, HRET 실행, 결과 집계 |
| Data Store | SQLite / PostgreSQL | sqlalchemy | 캐시, 태스크, 실험 데이터 저장 |
| Task Queue | Celery + Redis | celery, redis | 비동기 평가 태스크 관리 |

---

## 6. 데이터베이스 스키마 (Database Schema)

### 6.1 Leaderboard Cache
```sql
CREATE TABLE IF NOT EXISTS leaderboard_cache (
    model_name TEXT NOT NULL,
    language TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    task_type TEXT NOT NULL,
    score REAL NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_name, language, subject_type, task_type)
);
```

### 6.2 Evaluation Tasks
```sql
CREATE TABLE IF NOT EXISTS evaluation_tasks (
    task_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'STARTED', 'SUCCESS', 'FAILURE')),
    plan_details TEXT,
    result TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 6.3 Experiment Samples (실험 데이터)
```sql
CREATE TABLE IF NOT EXISTS experiment_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt TEXT NOT NULL,
  answer TEXT NOT NULL,
  skill_label TEXT NOT NULL,
  target_label TEXT NOT NULL,
  subject_label TEXT NOT NULL,
  format_label TEXT NOT NULL,
  dataset_name TEXT NOT NULL,
  meta_data TEXT,
  correctness REAL NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Repository 구조 (Repository Layout)

```text
benchhub-plus/
├── pyproject.toml
├── README.md
├── docker/
│   ├── backend.Dockerfile
│   ├── worker.Dockerfile
│   └── frontend.Dockerfile
├── deploy/
│   ├── docker-compose.yml
│   └── k8s/
│       ├── backend-deploy.yaml
│       ├── worker-deploy.yaml
│       └── frontend-deploy.yaml
├── apps/
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── stats.py
│   │   └── plan/planner.py
│   ├── backend/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── leaderboard.py
│   │   │   └── status.py
│   │   ├── services/orchestrator.py
│   │   └── repositories/
│   │       ├── leaderboard_repo.py
│   │       └── tasks_repo.py
│   ├── worker/
│   │   ├── celery_app.py
│   │   ├── tasks.py
│   │   └── hret_runner.py
│   ├── evaluation/
│   │   ├── adapters.py
│   │   ├── scoring.py
│   │   └── aggregation.py
│   └── frontend/
│       ├── app.py
│       └── components/
│           ├── forms.py
│           └── leaderboard.py
└── tests/
    ├── unit/
    └── integration/
```

---

## 8. 데이터 샘플링 및 집계 로직

- `experiment_samples`는 HRET 평가 시 생성되는 샘플 단위 결과 저장소.
- correctness는 [0,1] 실수값 (랜덤 혹은 채점 결과 기반)
- 리더보드 집계 시 평균 correctness를 사용:

```sql
SELECT
  dataset_name,
  skill_label,
  target_label,
  subject_label,
  format_label,
  AVG(correctness) AS score,
  COUNT(*) AS n
FROM experiment_samples
GROUP BY 1,2,3,4,5
ORDER BY score DESC;
```

---

## 9. 주요 설계 철학 및 문제의식

- **정적 리더보드의 한계:** 단일 점수로 모델을 비교하는 것은 의미가 없음.
- **동적·맞춤형 평가:** 사용자의 목적(예: 수학 문제 해결, 한국 문화 이해 등)에 맞는 랭킹 필요.
- **캐시-실시간 혼합 모델:** 빠른 응답성과 정확한 실험결과의 균형.
- **모델 독립성:** 사용자가 직접 API endpoint를 제공해 사내/비공개 모델 평가 가능.
- **재현성과 보안:** seed, benchhub_version, hret_version, prompt_version 명시 + API key 미저장.
- **확장성:** 모듈형 구성으로 향후 BenchHub, HRET 업데이트, 또는 도메인별 확장에 대응.

---

## 10. 시스템 요약 (TL;DR)

입력: 사용자 쿼리 + (선택) 모델명·API URL·API Key  
→ 플래너가 쿼리 해석해 평가 plan.yaml 생성  
→ 캐시 조회: 있으면 즉시 결과 반환  
→ 없으면 HRET 실행 태스크 큐 등록, 워커가 외부 API 모델 평가  
→ 완료 시 DB 저장 후 사용자 맞춤 리더보드 반환