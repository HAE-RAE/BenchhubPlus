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

6개의 대분류와 250개의 세부 분류로 이루어진 계층적 주제 분류 체계를 사용합니다.

#### 대분류 (6)

1. **Art & Sports**
2. **Culture**
3. **HASS**
4. **Science**
5. **Social Intelligence**
6. **Tech.**

#### 세부 분류 (250)

**Art & Sports (68개):**
- `Art & Sports/Architecture`
- `Art & Sports/Clothing`
- `Art & Sports/Education`
- `Art & Sports/Fashion`
- `Art & Sports/Festivals`
- `Art & Sports/Food`
- `Art & Sports/Language`
- `Art & Sports/Literature`
- `Art & Sports/Media`
- `Art & Sports/Music`
- `Art & Sports/Painting`
- `Art & Sports/Performing`
- `Art & Sports/Photography`
- `Art & Sports/Sculpture`
- `Art & Sports/Sports`
- `Art & Sports/Urban Eng.`
- `Art & Sports/arts&sports/animal`
- `Art & Sports/arts&sports/animal_life`
- `Art & Sports/arts&sports/animals`
- `Art & Sports/arts&sports/animation`
- `Art & Sports/arts&sports/anime`
- `Art & Sports/arts&sports/art`
- `Art & Sports/arts&sports/arts`
- `Art & Sports/arts&sports/artwork`
- `Art & Sports/arts&sports/barking`
- `Art & Sports/arts&sports/boat`
- `Art & Sports/arts&sports/branding`
- `Art & Sports/arts&sports/character`
- `Art & Sports/arts&sports/collecting`
- `Art & Sports/arts&sports/dance`
- `Art & Sports/arts&sports/design`
- `Art & Sports/arts&sports/digital_design`
- `Art & Sports/arts&sports/dog`
- `Art & Sports/arts&sports/dogs`
- `Art & Sports/arts&sports/drink`
- `Art & Sports/arts&sports/equestrian`
- `Art & Sports/arts&sports/fantasy`
- `Art & Sports/arts&sports/farming`
- `Art & Sports/arts&sports/fiction`
- `Art & Sports/arts&sports/fitness`
- `Art & Sports/arts&sports/flower`
- `Art & Sports/arts&sports/furniture`
- `Art & Sports/arts&sports/game`
- `Art & Sports/arts&sports/gaming`
- `Art & Sports/arts&sports/graphics`
- `Art & Sports/arts&sports/illustration`
- `Art & Sports/arts&sports/infographic`
- `Art & Sports/arts&sports/landscape`
- `Art & Sports/arts&sports/landscapes`
- `Art & Sports/arts&sports/nature`
- `Art & Sports/arts&sports/poetry`
- `Art & Sports/arts&sports/puzzle`
- `Art & Sports/arts&sports/reading`
- `Art & Sports/arts&sports/scenic`
- `Art & Sports/arts&sports/speech`
- `Art & Sports/arts&sports/toy`
- `Art & Sports/arts&sports/transportation`
- `Art & Sports/arts&sports/typography`
- `Art & Sports/arts&sports/urban`
- `Art & Sports/arts&sports/urban_art`
- `Art & Sports/arts&sports/urban_design`
- `Art & Sports/arts&sports/urban_environment`
- `Art & Sports/arts&sports/urban_life`
- `Art & Sports/arts&sports/urbanism`
- `Art & Sports/arts&sports/video_games`
- `Art & Sports/arts&sports/website`
- `Art & Sports/arts&sports/wine`
- `Art & Sports/arts&sports/zoology`

**Culture (14개):**
- `Culture/Celebration Holiday`
- `Culture/Clothing`
- `Culture/Daily Life`
- `Culture/Family`
- `Culture/Food`
- `Culture/Holiday`
- `Culture/Housing`
- `Culture/Leisure`
- `Culture/Tradition`
- `Culture/Work Life`
- `Culture/culture/attractions`
- `Culture/culture/friendship`
- `Culture/culture/hobbies`
- `Culture/culture/nature`

**HASS (68개):**
- `HASS/Administration`
- `HASS/Art & Sports`
- `HASS/Biology`
- `HASS/Celebration Holiday`
- `HASS/Cognitive Studies`
- `HASS/Culture`
- `HASS/Daily Life`
- `HASS/Economics`
- `HASS/Education`
- `HASS/Family`
- `HASS/Food`
- `HASS/Geography`
- `HASS/HASS`
- `HASS/History`
- `HASS/Language`
- `HASS/Law`
- `HASS/Literature`
- `HASS/Math`
- `HASS/Media`
- `HASS/Music`
- `HASS/Philosophy`
- `HASS/Physics`
- `HASS/Politics`
- `HASS/Psychology`
- `HASS/Religion`
- `HASS/Sports`
- `HASS/Tech.`
- `HASS/Trade`
- `HASS/Tradition`
- `HASS/Urban Eng.`
- `HASS/Welfare`
- `HASS/Work Life`
- `HASS/social&humanity/animal_welfare`
- `HASS/social&humanity/biography`
- `HASS/social&humanity/branding`
- `HASS/social&humanity/celebrity`
- `HASS/social&humanity/communication`
- `HASS/social&humanity/crime`
- `HASS/social&humanity/customer_support`
- `HASS/social&humanity/data_science`
- `HASS/social&humanity/database`
- `HASS/social&humanity/databases`
- `HASS/social&humanity/date`
- `HASS/social&humanity/dates`
- `HASS/social&humanity/datetime`
- `HASS/social&humanity/director`
- `HASS/social&humanity/drama`
- `HASS/social&humanity/environment`
- `HASS/social&humanity/fiction`
- `HASS/social&humanity/finance`
- `HASS/social&humanity/friendship`
- `HASS/social&humanity/health`
- `HASS/social&humanity/hero`
- `HASS/social&humanity/identity`
- `HASS/social&humanity/leadership`
- `HASS/social&humanity/library`
- `HASS/social&humanity/lifestyle`
- `HASS/social&humanity/management`
- `HASS/social&humanity/museum`
- `HASS/social&humanity/organizations`
- `HASS/social&humanity/privacy`
- `HASS/social&humanity/real_estate`
- `HASS/social&humanity/sociology`
- `HASS/social&humanity/technology`
- `HASS/social&humanity/transport`
- `HASS/social&humanity/transportation`
- `HASS/social&humanity/website`
- `HASS/social&humanity/workplace`

**Science (20개):**
- `Science/Astronomy`
- `Science/Atmospheric Science`
- `Science/Biology`
- `Science/Biomedical Eng.`
- `Science/Chemistry`
- `Science/Earth Science`
- `Science/Electrical Eng.`
- `Science/Geology`
- `Science/History`
- `Science/Language`
- `Science/Life Science`
- `Science/Math`
- `Science/Physics`
- `Science/Religion`
- `Science/Statistics`
- `Science/science/color`
- `Science/science/dna`
- `Science/science/dna2protein`
- `Science/science/numerology`
- `Science/science/plant`

**Social Intelligence (18개):**
- `Social Intelligence/Bias`
- `Social Intelligence/Commonsense`
- `Social Intelligence/Language`
- `Social Intelligence/Norms`
- `Social Intelligence/Value/Alignment`
- `Social Intelligence/misc/abstract`
- `Social Intelligence/misc/animal`
- `Social Intelligence/misc/cliche`
- `Social Intelligence/misc/color`
- `Social Intelligence/misc/diagnosis`
- `Social Intelligence/misc/durable`
- `Social Intelligence/misc/hate_crime`
- `Social Intelligence/misc/health`
- `Social Intelligence/misc/idiomatic_expression`
- `Social Intelligence/misc/norm`
- `Social Intelligence/misc/proverb`
- `Social Intelligence/misc/thinking`
- `Social Intelligence/misc/wellbeing`

**Tech. (62개):**
- `Tech./AI`
- `Tech./Aerospace Eng.`
- `Tech./Agricultural Eng.`
- `Tech./Biomedical Eng.`
- `Tech./Chemical Eng.`
- `Tech./Civil Eng.`
- `Tech./Coding`
- `Tech./Electrical Eng.`
- `Tech./Energy`
- `Tech./Environmental Eng.`
- `Tech./Food`
- `Tech./Geography`
- `Tech./IT`
- `Tech./Marine Eng.`
- `Tech./Materials Eng.`
- `Tech./Mechanics`
- `Tech./Nuclear Eng.`
- `Tech./Physics`
- `Tech./Urban Eng.`
- `Tech./tech/aircraft`
- `Tech./tech/airline`
- `Tech./tech/airlines`
- `Tech./tech/algorithm`
- `Tech./tech/animal`
- `Tech./tech/animal_welfare`
- `Tech./tech/animation`
- `Tech./tech/aquarium`
- `Tech./tech/automotive`
- `Tech./tech/aviation`
- `Tech./tech/azure`
- `Tech./tech/boat`
- `Tech./tech/cloud`
- `Tech./tech/communication`
- `Tech./tech/communications`
- `Tech./tech/cv`
- `Tech./tech/database`
- `Tech./tech/db`
- `Tech./tech/dice`
- `Tech./tech/ethereum`
- `Tech./tech/finance`
- `Tech./tech/financial`
- `Tech./tech/geo_loc`
- `Tech./tech/geolocation`
- `Tech./tech/graphics`
- `Tech./tech/ios`
- `Tech./tech/marine_biology`
- `Tech./tech/marine_eng`
- `Tech./tech/mobile`
- `Tech./tech/monitoring`
- `Tech./tech/network`
- `Tech./tech/ocr`
- `Tech./tech/office`
- `Tech./tech/programming`
- `Tech./tech/real_estate`
- `Tech./tech/remote_sensing`
- `Tech./tech/robotics`
- `Tech./tech/secure`
- `Tech./tech/security`
- `Tech./tech/transportation`
- `Tech./tech/uuid`
- `Tech./tech/vehicle`
- `Tech./tech/voice`

**예시:**
```json
{
  "subject_type": ["Tech.", "Tech./Coding"]
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
  "subject_type": ["Tech.", "Tech./Electrical Eng."],
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
    subject_type=["Science", "Science/Math"],
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
  "subject_type": ["Tech.", "Tech./Coding"],
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
      subject_type: ["Tech.", "Tech./Coding"]
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
  "subject_type": ["Science", "Science/Math", "Science/Physics"]
}
```

### 복합 필터 조합
```json
{
  "problem_type": "open-ended",
  "target_type": "Local",
  "subject_type": ["Culture", "Culture/Tradition"],
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
    "subject_type": "Tech.",
    "task_type": "Programming"
}

# BenchHub 포맷으로 변환
benchhub_config = PlanConfig(
    problem_type="MCQA",  # 과업에서 추론
    target_type="General",  # 기본값
    subject_type=["Tech.", "Tech./Coding"],  # 확장됨
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
   **해결:** `["Tech.", "Tech./Coding"]`와 같은 유효한 카테고리를 사용하세요.

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
