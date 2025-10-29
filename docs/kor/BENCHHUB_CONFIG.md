# BenchHub 구성 가이드

## 개요

이 문서는 BenchhubPlus에서 사용하는 BenchHub 데이터셋 구성 구조를 자세히 설명합니다. BenchHub 데이터셋은 다양한 차원을 기준으로 평가 문항을 분류하고 필터링할 수 있도록 체계적으로 설계되어 있습니다.

## 구성 필드

### 1. Problem Type (문항 형식, string)

평가 문항의 형식과 구조를 정의합니다.

**사용 가능한 값:**
- `Binary`: 예/아니오 또는 참/거짓 형태의 문제
- `MCQA`: 선택지가 있는 객관식 문제
- `short-form`: 짧은 서술형 답변을 요구하는 문제
- `open-ended`: 장문의 서술형 답변이 필요한 문제

**예시:**
```json
{
  "problem_type": "MCQA"
}
```

### 2. Target Type (평가 대상 범위, string)

문항이 보편적인 지식을 다루는지, 특정 문화/지역 지식을 다루는지를 지정합니다.

**사용 가능한 값:**
- `General`: 문화에 상관없이 적용 가능한 보편적 지식
- `Local`: 특정 문화 또는 지역에 특화된 지식

**예시:**
```json
{
  "target_type": "General"
}
```

### 3. Subject Type (주제 분류, list)

6개의 대분류와 64개의 세부 분류로 이루어진 계층적 주제 분류 체계를 사용합니다.

#### 대분류 (6)

1. **Science**
2. **Technology**
3. **Humanities and Social Science (HASS)**
4. **Arts & Sports**
5. **Culture**
6. **Social Intelligence**

#### 세부 분류 (64)

**Science (15개):**
- `Math/Algebra`
- `Math/Geometry`
- `Math/Statistics`
- `Math/Calculus`
- `Physics/Classical Mechanics`
- `Physics/Thermodynamics`
- `Physics/Electromagnetism`
- `Chemistry/General`
- `Chemistry/Organic`
- `Chemistry/Inorganic`
- `Biology/General`
- `Biology/Genetics`
- `Biology/Ecology`
- `Earth Science/Geology`
- `Earth Science/Meteorology`

**Technology (11개):**
- `Tech./Computer Science`
- `Tech./Electrical Eng.`
- `Tech./Mechanical Eng.`
- `Tech./Civil Eng.`
- `Tech./Chemical Eng.`
- `Tech./Materials Science`
- `Tech./Information Systems`
- `Tech./Robotics`
- `Tech./AI/ML`
- `Tech./Cybersecurity`
- `Tech./Data Science`

**Humanities and Social Science (14개):**
- `HASS/History`
- `HASS/Philosophy`
- `HASS/Literature`
- `HASS/Linguistics`
- `HASS/Psychology`
- `HASS/Sociology`
- `HASS/Anthropology`
- `HASS/Political Science`
- `HASS/Economics`
- `HASS/Geography`
- `HASS/Education`
- `HASS/Law`
- `HASS/International Relations`
- `HASS/Public Administration`

**Arts & Sports (10개):**
- `Arts/Visual Arts`
- `Arts/Music`
- `Arts/Theater`
- `Arts/Film`
- `Arts/Design`
- `Arts/Architecture`
- `Sports/General`
- `Sports/Team Sports`
- `Sports/Individual Sports`
- `Sports/Olympic Sports`

**Culture (9개):**
- `Culture/Korean Traditional`
- `Culture/East Asian`
- `Culture/Western`
- `Culture/World Cultures`
- `Culture/Religion`
- `Culture/Mythology`
- `Culture/Festivals`
- `Culture/Food`
- `Culture/Fashion`

**Social Intelligence (9개):**
- `Social/Communication`
- `Social/Ethics`
- `Social/Etiquette`
- `Social/Leadership`
- `Social/Teamwork`
- `Social/Conflict Resolution`
- `Social/Emotional Intelligence`
- `Social/Cultural Sensitivity`
- `Social/Professional Skills`

**예시:**
```json
{
  "subject_type": ["Technology", "Tech./Computer Science"]
}
```

### 4. Task Type (과업 유형, string)

문제를 해결하기 위해 요구되는 인지적 능력을 정의합니다.

**사용 가능한 값:**
- `Knowledge`: 사실 기반 지식 회상 및 검색
- `Reasoning`: 논리적 사고, 문제 해결, 추론
- `Value`: 가치 판단 및 윤리적 사고
- `Alignment`: 문화·사회적 정렬성 평가

**예시:**
```json
{
  "task_type": "Knowledge"
}
```

### 5. External Tool Usage (외부 도구 사용 여부, boolean)

문제를 해결하는 데 외부 도구나 자료가 필요한지 여부를 나타냅니다.

**사용 가능한 값:**
- `true`: 계산기, 검색 엔진, 참고 자료 등의 외부 도구가 필요
- `false`: 내부 지식과 추론만으로 해결 가능

**예시:**
```json
{
  "external_tool_usage": false
}
```

## 전체 구성 예시

다음은 BenchHub 구성의 전체 예시입니다.

```json
{
  "problem_type": "MCQA",
  "target_type": "General",
  "subject_type": ["Technology", "Tech./Electrical Eng."],
  "task_type": "Knowledge",
  "external_tool_usage": false
}
```

## BenchhubPlus에서의 사용

### 1. 계획 구성

```python
from apps.core.schemas import PlanConfig

plan = PlanConfig(
    problem_type="MCQA",
    target_type="General",
    subject_type=["Science", "Math/Algebra"],
    task_type="Reasoning",
    external_tool_usage=False,
    language="Korean",
    sample_size=100
)
```

### 2. 자연어 질의 처리

플래너 에이전트는 자연어 질의를 BenchHub 구성으로 자동 변환합니다.

**입력:** "한국어로 된 프로그래밍 문제를 잘 푸는 모델을 찾고 싶어"

**출력:**
```json
{
  "problem_type": "MCQA",
  "target_type": "General",
  "subject_type": ["Technology", "Tech./Computer Science"],
  "task_type": "Knowledge",
  "external_tool_usage": false,
  "language": "Korean",
  "sample_size": 100
}
```

### 3. HRET 연동

BenchHub 구성은 HRET 호환 포맷으로 자동 변환됩니다.

```yaml
datasets:
  - name: "benchhub_filtered"
    type: "benchhub"
    filters:
      problem_type: "MCQA"
      target_type: "General"
      subject_type: ["Technology", "Tech./Computer Science"]
      task_type: "Knowledge"
      external_tool_usage: false
      language: "Korean"
```

## 필터링 및 질의 예시

### 단일 주제 필터
```json
{
  "subject_type": ["Science"]
}
```

### 다중 주제 필터
```json
{
  "subject_type": ["Science", "Math/Algebra", "Physics/Classical Mechanics"]
}
```

### 복합 필터 조합
```json
{
  "problem_type": "open-ended",
  "target_type": "Local",
  "subject_type": ["Culture", "Culture/Korean Traditional"],
  "task_type": "Value",
  "external_tool_usage": false
}
```

## 유효성 검증

BenchhubPlus는 모든 BenchHub 구성을 자동으로 검증합니다.

- **Problem Type**: 4개의 유효한 값 중 하나여야 합니다.
- **Target Type**: `General` 또는 `Local` 중 하나여야 합니다.
- **Subject Type**: 사전에 정의된 카테고리만 포함해야 합니다.
- **Task Type**: 4가지 인지 능력 유형 중 하나여야 합니다.
- **External Tool Usage**: 불리언 값이어야 합니다.

유효하지 않은 구성은 구체적인 안내가 포함된 검증 오류를 발생시킵니다.

## 모범 사례

### 1. Subject Type 선택
- 폭넓은 평가에는 대분류를 사용하세요.
- 특정 도메인 테스트에는 세부 분류를 사용하세요.
- 종합적인 평가에는 여러 카테고리를 조합하세요.

### 2. Problem Type 매칭
- 객관식 지식 테스트에는 `MCQA`를 사용하세요.
- 추론 및 가치 평가에는 `open-ended`를 사용하세요.
- 간단한 분류 작업에는 `Binary`를 사용하세요.

### 3. Task Type 정렬
- `Knowledge` 과업은 `MCQA` 형식과 잘 맞습니다.
- `Reasoning` 과업은 `open-ended` 형식에서 효과적입니다.
- `Value`와 `Alignment` 과업은 주관적 평가가 필요합니다.

### 4. Target Type 고려사항
- 문화 특화 평가에는 `Local`을 사용하세요.
- 보편적 지식 평가에는 `General`을 사용하세요.
- 평가 언어와 대상 유형을 함께 고려하세요.

## 레거시 포맷 마이그레이션

기존 구성을 이전 포맷으로 보유하고 있다면 다음 마이그레이션 유틸리티를 활용하세요.

```python
from apps.core.schemas import PlanConfig

# 레거시 포맷
legacy_config = {
    "language": "Korean",
    "subject_type": "Technology",
    "task_type": "Programming"
}

# BenchHub 포맷으로 변환
benchhub_config = PlanConfig(
    problem_type="MCQA",  # 과업에서 추론
    target_type="General",  # 기본값
    subject_type=["Technology", "Tech./Computer Science"],  # 확장됨
    task_type="Knowledge",  # Programming을 매핑
    external_tool_usage=False,  # 기본값
    language=legacy_config["language"],
    sample_size=100
)
```

## 문제 해결

### 자주 발생하는 오류

1. **잘못된 Subject Type**
   ```
   ValueError: Invalid subject_type 'Programming'. Must be one of the BenchHub categories.
   ```
   **해결:** `["Technology", "Tech./Computer Science"]`와 같은 유효한 카테고리를 사용하세요.

2. **Subject Type이 비어 있음**
   ```
   ValueError: subject_type cannot be empty
   ```
   **해결:** 최소 하나의 유효한 주제 카테고리를 지정하세요.

3. **잘못된 Problem Type**
   ```
   ValueError: problem_type must be one of ['Binary', 'MCQA', 'short-form', 'open-ended']
   ```
   **해결:** 네 가지 유효한 문제 유형 중 하나를 사용하세요.

### 도움받기

BenchHub 구성에 대한 추가 지원이 필요하면 다음을 참고하세요.

1. 검증 오류 메시지의 안내를 확인합니다.
2. 전체 카테고리 목록은 `apps/core/schemas.py` 파일에서 확인합니다.
3. 제공된 예시 구성을 템플릿으로 사용합니다.
4. 검증 유틸리티로 구성을 사전 검증합니다.

---

**최종 업데이트**: 2024년 10월 29일
**버전**: 2.0
**호환성**: BenchhubPlus v2.0+
