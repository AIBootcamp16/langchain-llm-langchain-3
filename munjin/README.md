# 정책·지원금 AI Agent (Policy & Grant AI Assistant)

## 📋 프로젝트 개요

정부 정책·지원금 정보를 쉽게 탐색하고, **근거 기반 설명 + 자격 가능성 판단**까지 제공하는 AI 에이전트 웹 서비스입니다.

### 주요 기능
- 🔍 **정책 검색**: 지역, 카테고리, 키워드 기반 정책 검색
- 💬 **Q&A 멀티턴**: 특정 정책에 대한 상세 질의응답
- ✅ **자격 확인**: 체크리스트 기반 자격 조건 판정
- 📊 **근거 제공**: 모든 답변에 출처 명시
- 🌐 **웹검색 보강**: DB 부족 시 실시간 웹검색

## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI, Python 3.11
- **Workflow**: LangGraph
- **DB**: MySQL 8.0, Qdrant (Vector DB)
- **LLM**: OpenAI API
- **Embedding**: bge-m3 (BAAI/bge-m3)
- **Observability**: LangSmith

### Frontend
- **Framework**: Next.js
- **State**: Zustand
- **Style**: Tailwind CSS

### Infrastructure
- **Backend**: Docker + Cloudtype
- **Frontend**: Vercel
- **Monitoring**: LangSmith

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 레포지토리 클론
git clone <repository-url>
cd langgraph_project

# 환경변수 설정
cp env.example .env
# .env 파일을 열어 API 키 등을 설정하세요
```

### 2. Docker로 실행

```bash
# Docker 컨테이너 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
```

### 3. 데이터 적재

```bash
# 백엔드 컨테이너 접속
docker exec -it policy_backend bash

# 데이터 적재 스크립트 실행
python scripts/ingest_data.py
```

### 4. API 테스트

```bash
# Health check
curl http://localhost:8000/health

# API 문서 확인
open http://localhost:8000/docs
```

## 📁 프로젝트 구조

```
langgraph_project/
├── README.md                             # 프로젝트 개요, 기술스택, 빠른 시작 가이드
├── .env.example                          # 환경변수 템플릿 (DB, OpenAI, LangSmith 등)
├── .gitignore                            # Git 무시 파일
├── docker-compose.yml                    # mysql + qdrant + backend + adminer 컨테이너 구성
├── data.json                             # 508개 정책 데이터 (MySQL/Qdrant 적재용)
│
├── infra/                                # 인프라 설정
│   ├── mysql/
│   │   ├── init/
│   │   │   └── 001_init.sql             # 8개 테이블 스키마
│   │   └── my.cnf                        # MySQL 설정
│   └── cloudtype/
│       └── backend.Dockerfile            # Python 3.11 + FastAPI 컨테이너
│
├── backend/                               # FastAPI 백엔드
│   ├── requirements.txt                   # 22개 패키지 (fastapi, langgraph, qdrant, tavily 등)
│   ├── pytest.ini                         # Pytest 설정
│   ├── scripts/
│   │   └── ingest_data.py                # data.json → MySQL/Qdrant 적재 스크립트
│   └── src/app/
│       ├── main.py                       # FastAPI 앱 생성, CORS, 라우터 등록
│       │
│       ├── api/                          # API 라우터
│       │   ├── routes_chat.py           # POST /chat, POST /session/reset
│       │   ├── routes_policy.py         # GET /policies, GET /policy/{id}
│       │   ├── routes_eligibility.py    # POST /eligibility/start, /answer
│       │   ├── routes_web_source.py     # GET /web-source/{id}
│       │   └── routes_admin.py          # GET /health, /stats
│       │
│       ├── config/                       # 설정
│       │   ├── settings.py              # Pydantic Settings
│       │   └── logger.py                # 구조화된 JSON 로거
│       │
│       ├── domain/                       # Pydantic 모델
│       │   ├── policy.py                # PolicyResponse
│       │   ├── evidence.py              # Evidence, EvidenceType
│       │   ├── eligibility.py           # EligibilityStartRequest/Response
│       │   ├── chat.py                  # ChatRequest/Response
│       │   └── web_source.py            # WebSourceResponse
│       │
│       ├── db/                           # MySQL ORM & Repository
│       │   ├── engine.py                # SQLAlchemy 엔진
│       │   ├── models.py                # 8개 ORM 모델
│       │   └── repositories/
│       │       ├── policy_repo.py       # PolicyRepository
│       │       ├── session_repo.py      # SessionRepository
│       │       └── web_source_repo.py   # WebSourceRepository
│       │
│       ├── vector_store/                 # Qdrant + bge-m3
│       │   ├── qdrant_client.py         # QdrantClient
│       │   ├── embedder_bge_m3.py       # BGE-M3 임베딩 (1024차원)
│       │   └── chunker.py               # RecursiveCharacterTextSplitter
│       │
│       ├── web_search/                   # 웹 검색
│       │   └── clients/
│       │       ├── duckduckgo_client.py # DuckDuckGoClient
│       │       └── tavily_client.py     # TavilyClient
│       │
│       ├── llm/                          # OpenAI API
│       │   └── openai_client.py         # OpenAIClient
│       │
│       ├── prompts/                      # Jinja2 프롬프트 템플릿
│       │   ├── policy_qa_prompt.jinja2  # Q&A 답변 생성
│       │   ├── eligibility_prompt.jinja2 # 조건 파싱
│       │   └── eligibility_question.jinja2 # 체크리스트 질문 생성
│       │
│       ├── agent/                        # LangGraph 워크플로우
│       │   ├── state.py                 # QAState, EligibilityState
│       │   ├── controller.py            # QAController
│       │   ├── nodes/
│       │   │   ├── classify_node.py     # 쿼리 분류
│       │   │   ├── retrieve_node.py     # Qdrant 검색
│       │   │   ├── check_node.py        # 근거 충분성 판단
│       │   │   ├── web_search_node.py   # Tavily 웹 검색
│       │   │   ├── answer_node.py       # LLM 답변 생성
│       │   │   └── eligibility_nodes.py # 자격확인 5개 노드
│       │   └── workflows/
│       │       ├── qa_workflow.py       # Q&A StateGraph
│       │       └── eligibility_workflow.py # 자격확인 StateGraph
│       │
│       ├── services/                     # 비즈니스 로직
│       │   ├── policy_search_service.py # 하이브리드 검색
│       │   └── web_source_service.py    # 웹 검색 결과 저장
│       │
│       ├── observability/                # LangSmith 트레이싱
│       │   ├── langsmith_client.py      # LangSmithClient
│       │   ├── tracing.py               # 트레이싱 데코레이터
│       │   ├── tags.py                  # 태그 생성
│       │   └── redact.py                # PII 마스킹
│       │
│       └── tests/                        # Pytest 테스트
│           ├── conftest.py              # 테스트 설정
│           ├── test_api_policy.py       # 정책 API 테스트
│           ├── test_api_chat.py         # Q&A API 테스트
│           └── test_api_eligibility.py  # 자격확인 API 테스트
│
└── frontend/                             # Next.js 프론트엔드
    ├── package.json                      # 12개 패키지 (next, react, zustand, tailwindcss)
    ├── next.config.js                    # Next.js 설정
    ├── tailwind.config.js                # Tailwind 커스텀 색상
    ├── tsconfig.json                     # TypeScript 설정
    └── src/
        ├── app/                          # Next.js App Router
        │   ├── layout.tsx               # RootLayout
        │   ├── page.tsx                 # 화면1: Home (검색, 인기정책)
        │   ├── search/
        │   │   └── page.tsx             # 화면2: 검색결과
        │   ├── policy/[policyId]/
        │   │   ├── page.tsx             # 화면3: 정책 상세
        │   │   ├── qa/page.tsx          # 화면4: Q&A 챗봇
        │   │   └── eligibility/
        │   │       ├── start/page.tsx   # 화면5: 자격확인 시작
        │   │       ├── checklist/page.tsx # 화면6: 질문 답변
        │   │       └── result/page.tsx  # 화면7: 결과
        │   └── web-source/[sourceId]/
        │       └── page.tsx             # 화면8: 웹 근거 상세
        │
        ├── components/                   # React 컴포넌트
        │   ├── layout/
        │   │   ├── Header.tsx           # 헤더
        │   │   └── Footer.tsx           # 푸터
        │   ├── chat/
        │   │   ├── ChatPanel.tsx        # 채팅 패널
        │   │   ├── ChatBubble.tsx       # 말풍선
        │   │   └── ChatInput.tsx        # 입력
        │   ├── policy/
        │   │   ├── PolicyCard.tsx       # 정책 카드
        │   │   ├── PolicyList.tsx       # 정책 목록
        │   │   └── PolicySummary.tsx    # 정책 요약
        │   ├── eligibility/
        │   │   ├── ChecklistQuestion.tsx # 질문 카드
        │   │   ├── ChecklistProgress.tsx # 진행 바
        │   │   └── ChecklistResult.tsx  # 최종 결과
        │   └── common/
        │       ├── Button.tsx           # 재사용 버튼
        │       ├── Badge.tsx            # 뱃지
        │       ├── Modal.tsx            # 모달
        │       └── Spinner.tsx          # 로딩 스피너
        │
        ├── store/                        # Zustand 상태 관리
        │   ├── useSessionStore.ts       # 세션 상태
        │   ├── usePolicyStore.ts        # 정책 상태
        │   ├── useEligibilityStore.ts   # 자격확인 상태
        │   └── useUIStore.ts            # UI 상태
        │
        ├── lib/                          # 유틸리티
        │   ├── api.ts                   # API 클라이언트
        │   ├── routes.ts                # 라우트 헬퍼
        │   └── types.ts                 # TypeScript 타입
        │
        └── styles/
            └── globals.css              # Tailwind 기본 스타일
```

### 화면 구성

| 화면 | URL | 주요 기능 |
|------|-----|-----------|
| 화면1: Home | `/` | 검색 바, 인기 정책, 카테고리 필터 |
| 화면2: 검색결과 | `/search?query=...` | 정책 목록, 지역/카테고리 필터 |
| 화면3: 정책 상세 | `/policy/[id]` | 정책 요약, Q&A/자격확인 버튼 |
| 화면4: Q&A | `/policy/[id]/qa` | 채팅, 근거 표시, 웹 검색 |
| 화면5: 자격확인 시작 | `/policy/[id]/eligibility/start` | 자격확인 안내, 시작 버튼 |
| 화면6: 질문 답변 | `/policy/[id]/eligibility/checklist` | 체크리스트 질문, 진행률 |
| 화면7: 결과 | `/policy/[id]/eligibility/result` | 자격 판정, 조건별 통과/실패 |
| 화면8: 웹 근거 상세 | `/web-source/[id]` | 웹 검색 근거 상세, URL, 전체 내용 |

## 🔧 개발 환경 설정

### Backend 개발

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn src.app.main:app --reload --port 8000
```

### Frontend 개발

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 📊 데이터베이스 스키마

### MySQL 테이블
1. **policies**: 정책 메타 정보
2. **documents**: 정책 문서 (청킹용)
3. **sessions**: 멀티턴 세션 관리
4. **slots**: 사용자 입력 슬롯
5. **checklist_results**: 자격 확인 결과
6. **web_sources**: 웹검색 근거
7. **chat_history**: 채팅 이력

### Qdrant 컬렉션
- **policies**: 정책 문서 chunk 임베딩 (bge-m3, 1024차원)

## 🔍 API 엔드포인트

### Health Check
- `GET /health`: 헬스체크
- `GET /`: API 정보

### Policies
- `GET /api/v1/policies`: 정책 검색 (지역, 카테고리, 키워드 필터)
- `GET /api/v1/policy/{id}`: 정책 상세 조회
- `GET /api/v1/policies/regions`: 지역 목록
- `GET /api/v1/policies/categories`: 카테고리 목록

### Chat
- `POST /api/v1/chat`: Q&A 멀티턴 대화 (LangGraph 워크플로우)
- `POST /api/v1/session/reset`: 세션 초기화

### Eligibility
- `POST /api/v1/eligibility/start`: 자격 확인 시작
- `POST /api/v1/eligibility/answer`: 자격 확인 답변
- `GET /api/v1/eligibility/result/{session_id}`: 자격 확인 결과 조회
- `DELETE /api/v1/eligibility/session/{session_id}`: 세션 삭제

### Admin
- `GET /api/v1/admin/stats`: 서비스 통계

## 📈 LangSmith 모니터링

### 트레이싱 태그
- `env:development|production`: 환경
- `feature:Policy-Search|Q&A|Eligibility-Check`: 기능
- `policy:{policy_id}`: 정책 ID
- `session:{session_id}`: 세션 ID

### 평가 메트릭
- **Groundedness**: 근거 기반성 (≥ 0.9 목표)
- **Citation Rate**: 인용률 (≥ 0.95 목표)
- **Response Time**: 응답 시간 (< 3초 목표)

## 🐳 Docker 명령어

### 기본 명령어

```bash
# 모든 컨테이너 빌드 및 실행
docker-compose up -d

# 특정 서비스만 실행
docker-compose up -d mysql qdrant
docker-compose up -d backend

# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f backend    # 백엔드 로그
docker-compose logs -f mysql      # MySQL 로그
docker-compose logs -f qdrant     # Qdrant 로그
docker-compose logs -f adminer    # Adminer 로그
docker-compose logs -f            # 모든 서비스 로그

# 컨테이너 중지
docker-compose stop

# 특정 컨테이너만 재시작
docker-compose restart backend

# 컨테이너 삭제
docker-compose down

# 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v
```

### 컨테이너 접속

```bash
# 백엔드 컨테이너 접속
docker exec -it policy_backend bash

# MySQL 컨테이너 접속
docker exec -it policy_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD}

# 데이터 적재 (백엔드 컨테이너 내부에서)
docker exec -it policy_backend python scripts/ingest_data.py
```

### 데이터베이스 관리

```bash
# Adminer 접속 (MySQL GUI)
# 브라우저에서 http://localhost:8080 접속
# 서버: mysql
# 사용자: MYSQL_USER (.env 파일 참조)
# 비밀번호: MYSQL_PASSWORD (.env 파일 참조)
# 데이터베이스: MYSQL_DATABASE (.env 파일 참조)

# Qdrant 대시보드 접속
# 브라우저에서 http://localhost:6335/dashboard 접속
```

### 헬스체크 및 디버깅

```bash
# 헬스체크 상태 확인
docker inspect policy_backend | grep -A 5 Health
docker inspect policy_mysql | grep -A 5 Health
docker inspect policy_qdrant | grep -A 5 Health

# API 헬스체크
curl http://localhost:8000/health

# 컨테이너 리소스 사용량 확인
docker stats
```

## 🧪 테스트

```bash
# Backend 테스트
cd backend
pytest

# Frontend 테스트
cd frontend
npm test
```

## 📝 환경변수

### Backend (.env)
```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=policies

# OpenAI
OPENAI_API_KEY=sk-...

# LangSmith
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=policy-qa-agent
LANGSMITH_TRACING=true
```



