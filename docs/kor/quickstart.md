# 빠른 시작 가이드

이 가이드는 BenchHub Plus를 몇 분 안에 실행하기 위한 핵심 절차를 정리합니다.

## 🚀 5분 설치 요약

### 사전 준비
- Docker 및 Docker Compose 설치
- OpenAI API 키(또는 기타 모델 API 키)

### 1단계: 저장소 클론 및 초기화
```bash
# 저장소 클론
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# 셋업 스크립트 실행
./scripts/setup.sh
```

### 2단계: 환경 변수 설정
```bash
# 환경 변수 템플릿 복사
cp .env.example .env

# API 키 편집
nano .env
```

**필수 설정:**
```env
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_PASSWORD=secure_password_here
```

### 3단계: 서비스 배포
```bash
# 모든 서비스 시작
./scripts/deploy.sh development
```

### 4단계: 애플리케이션 접속
- **프런트엔드**: http://localhost:8502
- **API 문서**: http://localhost:8001/docs
- **헬스 체크**: http://localhost:8001/api/v1/health

## 🎯 첫 번째 평가 실행

### 1. 웹 인터페이스 열기
브라우저에서 http://localhost:8502 로 접속합니다.

### 2. 첫 평가 생성
1. **"Evaluate" 탭 이동**
2. **질의 입력**: "Compare GPT-4 on basic math problems"
3. **모델 구성**
   - 이름: `gpt-4`
   - API Base: `https://api.openai.com/v1`
   - API Key: OpenAI API 키
   - Model Type: `openai`
4. **"🚀 Start Evaluation" 클릭**

### 3. 진행 상황 모니터링
1. **"Status" 탭으로 이동**
2. **평가 진행 상황 확인**
3. **완료 후 결과 열람**

### 4. 결과 살펴보기
1. **"Browse" 탭 이동**
2. **리더보드 결과 탐색**
3. **필터 및 정렬 옵션 활용**

## 📊 예시 질의

다음 예시 질의를 사용해 보세요.

### 기본 예시
```
"Test basic math skills with simple arithmetic"
"Compare reading comprehension in English"
"Evaluate code generation for Python"
```

### 고급 예시
```
"Compare these models on Korean high school math problems"
"Evaluate scientific reasoning in chemistry and physics"
"Test creative writing abilities with storytelling prompts"
```

## 🔧 주요 설정 팁

### 다중 모델 비교
여러 모델을 비교하려면 모델 설정을 추가합니다.
```json
{
  "query": "Compare multiple models on math problems",
  "models": [
    {
      "name": "gpt-4",
      "api_base": "https://api.openai.com/v1",
      "api_key": "sk-...",
      "model_type": "openai"
    },
    {
      "name": "claude-3",
      "api_base": "https://api.anthropic.com",
      "api_key": "sk-ant-...",
      "model_type": "anthropic"
    }
  ]
}
```

### 맞춤 평가 설정
다음 옵션으로 평가를 세밀하게 조정할 수 있습니다.
- **언어**: English, Korean 등
- **주제**: Math, Science, Literature 등
- **난이도**: Elementary, High School, University
- **샘플 수**: 10-1000
- **지표**: Accuracy, F1 Score 등

## 🚨 트러블슈팅

### 서비스가 시작되지 않을 때
```bash
# Docker 상태 확인
docker --version
docker-compose --version

# 로그 확인
docker-compose logs -f
```

### API 키 오류
1. API 키 값이 올바른지 확인합니다.
2. 키 권한을 확인합니다.
3. 사용 가능한 크레딧/쿼터를 확인합니다.

### 성능이 느릴 때
1. 샘플 수를 10-50으로 줄여 시작합니다.
2. 네트워크 상태를 확인합니다.
3. API 호출 제한을 모니터링합니다.

### 데이터베이스 문제
```bash
# 데이터베이스 초기화
docker-compose down -v
docker-compose up -d
```

## 📚 다음 단계

### 더 알아보기
- [사용자 매뉴얼](user-manual.md) - 전체 사용 가이드
- [API 레퍼런스](api-reference.md) - REST API 문서
- [개발 가이드](development.md) - 개발 환경 구성

### 고급 기능
- **커스텀 데이터셋**: 자체 평가 데이터 업로드
- **배치 평가**: 여러 평가 동시 실행
- **커스텀 지표**: 특화된 평가 지표 정의
- **결과 내보내기**: 분석용 결과 다운로드

### 연동 기능
- **API 연동**: 애플리케이션에서 REST API 사용
- **웹훅**: 평가 완료 알림
- **커스텀 모델**: 신규 모델 제공자 추가

## 🤝 지원 받기

### 빠른 도움
- **시스템 상태**: 웹 인터페이스의 "System" 탭 확인
- **로그**: `docker-compose logs -f`
- **헬스 체크**: http://localhost:8001/api/v1/health 방문

### 커뮤니티 지원
- **GitHub Issues**: 버그 신고 및 기능 제안
- **Discussions**: 질문 공유 및 토론
- **문서**: 전체 문서 열람

### 전문 지원
- **엔터프라이즈 지원**: 운영 환경 전용 지원
- **커스텀 개발**: 요구 사항에 맞춘 기능 개발
- **교육**: 팀 교육 및 온보딩 세션
