# BenchHub Plus 문서

BenchHub Plus는 자연어 질의를 맞춤형 모델 랭킹으로 변환하는 대화형 리더보드 시스템입니다. FastAPI 백엔드, 현대적인 Reflex 프런트엔드, Celery 워커, HRET 통합으로 구성되어 동적인 LLM 평가를 손쉽게 수행할 수 있습니다.

## 📚 문서 색인

### 시작하기
- [설치 및 설정 가이드](SETUP_GUIDE.md) - **전체 설치·설정 절차 안내**
- [설치 안내](installation.md) - 기존 설치 절차 정리
- [빠른 시작](quickstart.md) - 몇 분 만에 서비스 실행
- [실행 로그](EXECUTION_LOG.md) - 실제 실행 과정과 트러블슈팅 기록

### 사용자 가이드
- [사용자 매뉴얼](user-manual.md) - 전체 기능 설명
- [API 레퍼런스](api-reference.md) - REST API 문서
- [Reflex 마이그레이션 가이드](reflex-migration.md) - **새로운 Reflex 프런트엔드 사용법**
- [프런트엔드 가이드](frontend-guide.md) - Streamlit 인터페이스 사용법 (TODO: 추가 예정)

### 개발
- [개발 가이드](development.md) - 개발 환경 구축과 규칙
- [아키텍처](architecture.md) - 시스템 구조와 설계
- [기여 가이드](contributing.md) - 프로젝트 기여 방법 (TODO: 추가 예정)

### 배포
- [Docker 배포](docker-deployment.md) - Docker 기반 배포 안내
- [프로덕션 설정](production-setup.md) - 운영 환경 구성 방법 (TODO: 추가 예정)
- [모니터링](monitoring.md) - 시스템 모니터링과 유지보수 (TODO: 추가 예정)

### 고급 주제
- [BenchHub 구성](BENCHHUB_CONFIG.md) - **BenchHub 구성 파일 구조와 통합 방법**
- [HRET 통합](HRET_INTEGRATION.md) - **HRET 툴킷 통합 가이드**
- [사용자 정의 평가](custom-evaluations.md) - 맞춤 평가 시나리오 작성법 (TODO: 추가 예정)
- [문제 해결](troubleshooting.md) - 자주 발생하는 오류와 해결책

## 🚀 바로가기

- **라이브 데모**: [Demo Link] (TODO: 데모 링크 추가 예정)
- **GitHub 저장소**: [HAE-RAE/BenchhubPlus](https://github.com/HAE-RAE/BenchhubPlus)
- **이슈 트래커**: [GitHub Issues](https://github.com/HAE-RAE/BenchhubPlus/issues)
- **토론**: [GitHub Discussions](https://github.com/HAE-RAE/BenchhubPlus/discussions)

## 🏗️ 시스템 개요

BenchHub Plus는 다음과 같은 흐름으로 동작합니다.

1. **자연어 질의 입력**: 사용자가 평가 요구사항을 자연어로 작성합니다.
2. **평가 계획 생성**: AI 기반 플래너가 질의를 구조화된 평가 계획으로 변환합니다.
3. **평가 실행**: 분산 워커 시스템이 HRET 툴킷을 이용해 평가를 수행합니다.
4. **결과 제공**: 실시간 리더보드와 상세 분석 리포트를 제공합니다.

### 핵심 기능

- 🤖 **AI 기반 계획 수립**: 자연어를 평가 계획으로 자동 변환
- 🏆 **동적인 리더보드**: 실시간 순위 갱신
- 🔄 **비동기 처리**: 확장 가능한 백그라운드 작업 처리
- 📊 **풍부한 시각화**: 인터랙티브 차트와 분석 지표
- 🐳 **Docker 대응**: 완전한 컨테이너 배포 지원
- 🔌 **확장성**: 맞춤 평가 플러그인 구조 지원

## 🛠️ 기술 스택

- **백엔드**: FastAPI, SQLAlchemy, PostgreSQL
- **프런트엔드**: Reflex (권장), Streamlit (레거시 지원), Plotly
- **작업 큐**: Celery, Redis
- **평가**: HRET Toolkit
- **배포**: Docker, Docker Compose
- **AI/ML**: OpenAI API, 커스텀 LLM 연동

## 📖 도움받기

- **문서 관련 이슈**: `documentation` 라벨을 달아 이슈 등록
- **버그 신고**: 버그 리포트 템플릿 사용
- **기능 제안**: 기능 제안 템플릿 사용
- **일반 질문**: Discussions에서 질문 시작

## 📄 라이선스

이 프로젝트는 MIT License를 따릅니다. 자세한 내용은 [LICENSE](../LICENSE) 파일을 참고하세요.


