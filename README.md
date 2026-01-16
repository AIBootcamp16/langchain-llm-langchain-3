<p align="center">
  <img
    src="https://capsule-render.vercel.app/api?type=soft&height=200&text=🗂️%20정책·지원금%20AI%20Agent&fontSize=35&desc=3조%20SEARCHSPARK&descSize=22&descAlignY=70&color=gradient&customColorList=0,2,6,11,20&fontColor=ffffff&animation=fadeIn"
    alt="정책 문서를 이해하고 답변하는 정책·지원금 AI Agent - 3조 SEARCHSPARK"
  />
</p>

<p align="center">
  정부 정책·지원금 정보를 쉽게 탐색하고, **근거 기반 설명 + 자격 가능성 판단**까지 제공하는 AI 에이전트 웹 서비스입니다.
</p>

<div align="center">
  <a href="https://github.com/AIBootcamp16/langchain-llm-langchain-3">
    <img src="https://img.shields.io/github/stars/AIBootcamp16/langchain-llm-langchain-3?style=social" alt="GitHub stars"/>
  </a>
  <a href="https://github.com/AIBootcamp16/langchain-llm-langchain-3">
    <img src="https://img.shields.io/github/forks/AIBootcamp16/langchain-llm-langchain-3?style=social" alt="GitHub forks"/>
  </a>
</div>

<br>

## 👨‍👩‍👦‍👦 팀 구성원

<div align="center">

<table>
<tr>
<td align="center" width="200px">
  <a href="https://github.com/moongs95"><img src="https://avatars.githubusercontent.com/moongs95" width="200px;" alt="권문진"/></a>
</td>
<td align="center" width="200px">
  <a href="https://github.com/realtheai"><img src="https://avatars.githubusercontent.com/realtheai" width="200px;" alt="손은혜"/></a>
</td>
<td align="center" width="200px">
  <a href="https://github.com/imeanseo"><img src="https://avatars.githubusercontent.com/imeanseo" width="200px;" alt="고민서"/></a>
</td>
<td align="center" width="200px">
  <a href="https://github.com/parkjunsu3321"><img src="https://avatars.githubusercontent.com/parkjunsu3321" width="200px;" alt="박준수"/></a>
</td>
</tr>
<tr>
<td align="center"><a href="https://github.com/moongs95"><b>🌟 권문진</b></a></td>
<td align="center"><a href="https://github.com/realtheai"><b>🌟 손은혜</b></a></td>
<td align="center"><a href="https://github.com/imeanseo"><b>🌟 고민서</b></a></td>
<td align="center"><a href="https://github.com/parkjunsu3321"><b>🌟 박준수</b></a></td>
</tr>
<tr>
<td align="center">
  <sub><b>📌 데이터 수집 및 정제<br>
  검색 시스템 구조 설계<br>
  Hybrid Search 구현<br>
  검색 품질 및 성능 개선</b></sub><br>
</td>
<td align="center">
  <sub><b>📌 기획<br>
  아키텍처 설계<br>
  DB<br>
  백엔드/프론트엔드<br>
  QA Agent 설계<br>
  코드 통합</b></sub><br>
</td>
<td align="center">
  <sub><b>📌 데이터 수집 및 정제<br>
  Search Agent팀 기획 및 깃 정리<br>
  Search Agent 설계 및 개발<br>
  검색 품질 및 성능 정리</b></sub><br>
</td>
<td align="center">
  <sub><b>📌 Eligibility Agent 설계<br>
  자격 검증 기능 구현<br>
  질문지 작성 기능 구현<br>
  데이터 수집 및 정제</b></sub><br>
</td>
</tr>
</table>

<table>
<tr>
<td align="center" width="200px">
  <a href="https://github.com/hopeplanting"><img src="https://avatars.githubusercontent.com/hopeplanting" width="200px;" alt="권효주"/></a>
</td>
<td align="center" width="200px">
  <a href="https://github.com/Leesoomin97"><img src="https://avatars.githubusercontent.com/Leesoomin97" width="200px;" alt="이수민"/></a>
</td>
<td align="center" width="200px">
  <a href="https://github.com/juny79"><img src="https://avatars.githubusercontent.com/juny79" width="200px;" alt="박준영"/></a>
</td>
<td align="center" width="200px">
  <a href="https://github.com/yekyung821"><img src="https://avatars.githubusercontent.com/yekyung821" width="200px;" alt="허예경"/></a>
</td>
</tr>
<tr>
<td align="center"><a href="https://github.com/hopeplanting"><b>🌟 권효주</b></a></td>
<td align="center"><a href="https://github.com/Leesoomin97"><b>🌟 이수민</b></a></td>
<td align="center"><a href="https://github.com/juny79"><b>🌟 박준영</b></a></td>
<td align="center"><a href="https://github.com/yekyung821"><b>🌟 허예경</b></a></td>
</tr>
<tr>
<td align="center">
  <sub><b>📌 데이터 수집 및 정제<br>
  Search Agent 설계·개발<br>
  문제 분석 및 성능 개선</b></sub><br>
</td>
<td align="center">
  <sub><b>📌 데이터 수집 및 정제<br>
  Eligibility Agent 로직 설계<br>
  자격 검증 기능 구현</b></sub><br>
</td>
<td align="center">
  <sub><b>📌 데이터 모니터링 및 정제</b></sub><br>
  QA Agent 품질 및 성능 테스트<br>
</td>
<td align="center">
  <sub><b>📌 데이터 정제 및 병합<br>
  지원 대상 조건 분류 및 정형화<br>
  Eligibility Agent 로직 설계 및 구현</b></sub><br>
</td>
</tr>
</table>

</div>

<br>


### 주요 기능
- 🔍 **하이브리드 검색**: Dense(BGE-M3) + Sparse(BM25) 검색, 지역/카테고리 필터링, 웹 검색 통합
- 💬 **Q&A 멀티턴**: LangGraph 기반 대화형 정책 Q&A, 실시간 스트리밍 응답
- ⚡ **인메모리 캐싱**: 정책 문서 및 대화 히스토리 캐싱으로 빠른 응답 속도
- ✅ **자격 확인 Agent**: 대화형 체크리스트로 정책 자격 조건 자동 판정
- 📊 **근거 기반 답변**: 모든 답변에 출처 명시 ([정책문서 X], [웹 X])
- 🌐 **웹 검색 보강**: Tavily API를 통한 실시간 웹 검색, DB 부족 시 자동 보완

## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI, Python 3.11
- **Workflow**: LangGraph (조건부 라우팅, 상태 관리)
- **DB**: MySQL 8.0 (정책 메타데이터), Qdrant (Vector DB)
- **Search**: BGE-M3 (Dense), BM25 (Sparse), Reciprocal Rank Fusion
- **LLM**: OpenAI GPT-4o-mini
- **Web Search**: Tavily API
- **Cache**: In-memory (Chat History, Policy Documents)
- **Observability**: LangSmith (Tracing, Evaluation)

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
│   ├── requirements.txt                   # Python 패키지 (fastapi, langgraph, qdrant, tavily 등)
│   ├── scripts/
│   │   └── ingest_data.py                # data.json → MySQL/Qdrant 적재 스크립트
│   └── src/app/
│       ├── main.py                       # FastAPI 앱 생성, CORS, 라우터 등록
│       │
│       ├── api/                          # API 라우터
│       │   ├── routes_chat.py           # POST /chat/stream (SSE), POST /chat/init, DELETE /chat/cleanup
│       │   ├── routes_policy.py         # GET /policies/search, GET /policies/{id}, GET /regions, /categories
│       │   ├── routes_eligibility.py    # POST /eligibility/start, /answer, /result
│       │   └── routes_admin.py          # GET /health, /stats
│       │
│       ├── config/                       # 설정
│       │   ├── settings.py              # Pydantic Settings (환경변수 관리)
│       │   └── logger.py                # 구조화된 JSON 로거
│       │
│       ├── domain/                       # Pydantic 모델
│       │   ├── policy.py                # PolicyResponse, SearchParams
│       │   ├── evidence.py              # Evidence, EvidenceType
│       │   ├── eligibility.py           # EligibilityStartRequest/Response
│       │   └── chat.py                  # ChatRequest/Response
│       │
│       ├── db/                           # MySQL ORM & Repository
│       │   ├── engine.py                # SQLAlchemy 엔진
│       │   ├── models.py                # ORM 모델 (Policy, Session, ChatHistory 등)
│       │   └── repositories/
│       │       ├── policy_repo.py       # PolicyRepository (정책 CRUD)
│       │       └── session_repo.py      # SessionRepository (세션 관리)
│       │
│       ├── cache/                        # 인메모리 캐싱
│       │   ├── chat_cache.py            # ChatCache (대화 히스토리)
│       │   └── policy_cache.py          # PolicyCache (정책 문서)
│       │
│       ├── vector_store/                 # Qdrant + Embedding
│       │   ├── qdrant_client.py         # QdrantClient (벡터 검색)
│       │   ├── embedder_bge_m3.py       # BGE-M3 임베딩 (1024차원)
│       │   ├── sparse_search.py         # BM25 키워드 검색 + RRF
│       │   └── chunker.py               # RecursiveCharacterTextSplitter
│       │
│       ├── web_search/                   # 웹 검색
│       │   └── clients/
│       │       └── tavily_client.py     # TavilyClient (실시간 웹 검색)
│       │
│       ├── llm/                          # OpenAI API
│       │   └── openai_client.py         # OpenAIClient (GPT-4o-mini)
│       │
│       ├── prompts/                      # Jinja2 프롬프트 템플릿
│       │   ├── classify_prompt.jinja2   # 쿼리 분류
│       │   ├── check_prompt.jinja2      # 근거 충분성 판단
│       │   ├── policy_qa_docs_only_prompt.jinja2  # 정책 문서 기반 답변
│       │   ├── policy_qa_web_only_prompt.jinja2   # 웹 검색 기반 답변
│       │   ├── policy_qa_hybrid_prompt.jinja2     # 하이브리드 답변
│       │   ├── eligibility_prompt.jinja2          # 자격 조건 파싱
│       │   ├── eligibility_question.jinja2        # 자격 확인 질문 생성
│       │   └── eligibility_judge.jinja2           # 자격 판정
│       │
│       ├── agent/                        # LangGraph 워크플로우
│       │   ├── state.py                 # QAState, EligibilityState (TypedDict)
│       │   ├── controller.py            # AgentController (run_qa, run_search)
│       │   ├── nodes/
│       │   │   ├── classify_node.py     # 쿼리 분류 (general/specific/comparative)
│       │   │   ├── retrieve_node.py     # 캐시에서 정책 문서 로드
│       │   │   ├── check_node.py        # 근거 충분성 판단
│       │   │   ├── web_search_node.py   # Tavily 웹 검색
│       │   │   ├── answer_node.py       # LLM 답변 생성 (3가지 경로)
│       │   │   └── eligibility_nodes.py # 자격확인 노드 (parse, check, question, process, final_decision)
│       │   └── workflows/
│       │       ├── qa_workflow.py       # Q&A StateGraph (조건부 라우팅)
│       │       └── eligibility_workflow.py # 자격확인 StateGraph
│       │
│       ├── services/                     # 비즈니스 로직
│       │   ├── simple_search_service.py # SimpleSearchService (하이브리드 검색)
│       │   ├── search_config.py         # SearchConfig (동적 임계값 조정)
│       │   └── policy_search_service.py # PolicySearchService (Legacy, 상세 조회용)
│       │
│       ├── observability/                # LangSmith 트레이싱
│       │   ├── langsmith_client.py      # LangSmithClient 초기화
│       │   ├── tracing.py               # @trace_workflow 데코레이터
│       │   ├── tags.py                  # 태그 생성 (env, feature, policy_id, session_id)
│       │   └── redact.py                # PII 마스킹
│       │
│       └── evaluation/                   # LangSmith 평가
│           ├── datasets.py              # 평가 데이터셋 정의 (8개 테스트 케이스)
│           ├── evaluators.py            # 평가 메트릭 (5개)
│           ├── upload_dataset.py        # 데이터셋 업로드 스크립트
│           └── run_evaluation.py        # 평가 실행 스크립트
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

### Policies (검색)
- `GET /api/v1/policies/search`: **하이브리드 검색** (query, region, category, target_group)
  - Dense (BGE-M3) + Sparse (BM25) + RRF
  - 웹 검색 자동 통합 (Tavily)
- `GET /api/v1/policies/{id}`: 정책 상세 조회
- `GET /api/v1/policies/regions`: 지역 목록
- `GET /api/v1/policies/categories`: 카테고리 목록

### Chat (Q&A Agent)
- `POST /api/v1/chat/stream`: **SSE 스트리밍** Q&A (LangGraph 워크플로우)
  - 실시간 답변 스트리밍
  - 상태 업데이트 (분류 → 검색 → 판단 → 답변)
  - Evidence 제공
- `POST /api/v1/chat/init`: 정책 문서 캐시 초기화
- `DELETE /api/v1/chat/cleanup`: 세션 캐시 정리

### Eligibility (자격 확인 Agent)
- `POST /api/v1/eligibility/start`: 자격 확인 시작 (정책 조건 파싱)
- `POST /api/v1/eligibility/answer`: 사용자 답변 처리 (다음 질문 or 최종 판정)
- `POST /api/v1/eligibility/result`: 최종 자격 판정 결과 조회

### Admin
- `GET /api/v1/admin/stats`: 서비스 통계

## 📈 LangSmith 모니터링 & 평가

### 트레이싱 (Observability)
**태그 시스템**:
- `env:development|production`: 환경
- `feature:SEARCH|QA|EC`: 기능 (Search, Q&A, Eligibility Check)
- `policy:{policy_id}`: 정책 ID
- `session:{session_id}`: 세션 ID

**트레이싱 범위** (총 21개):

**QA Agent** (10개):
- ✅ `run_qa` - 전체 워크플로우 컨트롤러
- ✅ `create_qa_workflow` - 워크플로우 그래프 생성
- ✅ `run_qa_workflow` - 워크플로우 실행
- ✅ `classify_query_type_node` - 쿼리 타입 분류 (`run_type="chain"`)
- ✅ `load_cached_docs_node` - 캐시에서 문서 로드 (`run_type="retriever"`)
- ✅ `check_sufficiency_node` - 근거 충분성 판단 (`run_type="chain"`)
- ✅ `web_search_node` - Tavily 웹 검색 (`run_type="tool"`)
- ✅ `generate_answer_with_docs_node` - 문서 기반 답변 (`run_type="llm"`)
- ✅ `generate_answer_web_only_node` - 웹 검색 기반 답변 (`run_type="llm"`)
- ✅ `generate_answer_hybrid_node` - 하이브리드 답변 (`run_type="llm"`)

**Eligibility Agent** (10개):
- ✅ `create_eligibility_start_workflow` - 시작 워크플로우 생성
- ✅ `create_eligibility_answer_workflow` - 답변 워크플로우 생성
- ✅ `run_eligibility_start` - 자격 확인 시작
- ✅ `run_eligibility_answer` - 사용자 답변 처리
- ✅ `run_eligibility_result` - 최종 판정 결과
- ✅ `parse_conditions_node` - 자격 조건 파싱 (`run_type="llm"`)
- ✅ `check_existing_slots_node` - 기존 슬롯 확인 (`run_type="chain"`)
- ✅ `generate_question_node` - 질문 생성 (`run_type="llm"`)
- ✅ `process_answer_node` - 답변 처리 및 판정 (`run_type="chain"`)
- ✅ `final_decision_node` - 최종 결정 (`run_type="chain"`)

**Search API** (1개):
- ✅ `run_search` - 하이브리드 검색 실행

**LangSmith에서 확인 가능한 정보**:
- 각 노드별 실행 시간 및 병목 구간
- LLM 호출 내역 (프롬프트, 응답, 토큰 수)
- 검색 결과 및 캐시 히트율
- 에러 발생 시 상세 스택 트레이스
- 전체 워크플로우 실행 흐름 시각화

### 평가 (Evaluation) 
**데이터셋**: 8개 테스트 케이스 (일반 질문, 근거 부족, 비교 질문 등)

**메트릭** (5개):
1. **Groundedness**: 근거 기반성 (≥ 0.9 목표)
   - 답변이 제공된 문서/웹 검색 결과에 기반하는지 평가
2. **Citation Rate**: 인용률 (≥ 0.95 목표)
   - 답변에 [정책문서 X], [웹 X] 인용이 포함되었는지
3. **Response Time**: 응답 시간 (< 3초 목표)
4. **Relevance**: 답변 관련성
   - 질문과 답변의 관련도 평가
5. **Completeness**: 답변 완전성
   - 질문에 대한 충분한 정보 제공 여부

**실행 방법**:
```bash
# 데이터셋 업로드
python backend/src/app/evaluation/upload_dataset.py

# 평가 실행
python backend/src/app/evaluation/run_evaluation.py
```

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

## 📝 환경변수

### Backend (.env)
```bash
# MySQL Database
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=policy_db
MYSQL_USER=policy_user
MYSQL_PASSWORD=your_password
MYSQL_ROOT_PASSWORD=root_password

# Qdrant Vector DB
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=policies
QDRANT_API_KEY=  # Optional

# OpenAI API
OPENAI_API_KEY=sk-...

# Tavily Web Search
TAVILY_API_KEY=tvly-...

# LangSmith (Tracing & Evaluation)
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=policy-qa-agent
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Application Settings
APP_ENV=development  # development | production
LOG_LEVEL=INFO
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🏗️ 주요 아키텍처 특징

### 1. 하이브리드 검색 시스템
**SimpleSearchService** (`backend/src/app/services/simple_search_service.py`)
- **Dense Search**: BGE-M3 임베딩 + Qdrant 벡터 검색
- **Sparse Search**: BM25 키워드 검색
- **Reciprocal Rank Fusion**: Dense + Sparse 결과 통합
- **동적 임계값 조정**: 검색 결과 수에 따라 similarity threshold 자동 조정
- **웹 검색 통합**: Tavily API를 통한 실시간 웹 검색 (DB 부족 시)
- **필터링**: 지역, 카테고리, 대상 그룹별 필터링

### 2. LangGraph 기반 Q&A Agent
**QA Workflow** (`backend/src/app/agent/workflows/qa_workflow.py`)
```
START → Classify → Retrieve → Check → [Answer_DocsOnly | Web_Search → Answer_Hybrid | Answer_WebOnly] → END
```

**조건부 라우팅**:
- `Classify`: 쿼리 타입 분류 (general/specific/comparative)
- `Check`: 정책 문서만으로 답변 가능한지 판단
  - 충분함 → `Answer_DocsOnly`
  - 불충분 → `Web_Search` → `Answer_Hybrid`
  - 문서 없음 → `Answer_WebOnly`

**인메모리 캐싱**:
- `ChatCache`: 대화 히스토리 캐싱 (멀티턴 지원)
- `PolicyCache`: 정책 문서 캐싱 (Qdrant 호출 최소화)

### 3. Eligibility Check Agent
**대화형 자격 확인** (`backend/src/app/agent/workflows/eligibility_workflow.py`)

**시작 워크플로우** (Start Workflow):
```
START → Parse_Conditions → Check_Existing_Slots → Generate_Question → END
```

**답변 워크플로우** (Answer Workflow):
```
START → Process_Answer → [조건 판단] → [Generate_Question | Final_Decision] → END
```

**노드 역할**:
- `Parse_Conditions`: `apply_target` 텍스트를 구조화된 조건으로 파싱 (LLM)
- `Check_Existing_Slots`: 기존 사용자 정보로 판단 가능한 조건 자동 체크
- `Generate_Question`: LLM으로 간결한 질문 생성
- `Process_Answer`: 사용자 답변 처리 및 PASS/FAIL/UNKNOWN 판정 (LLM)
- `Final_Decision`: 모든 조건 종합 후 최종 자격 판정 (ELIGIBLE/NOT_ELIGIBLE)

### 4. SSE 스트리밍 응답
**실시간 답변** (`backend/src/app/api/routes_chat.py`)
- Server-Sent Events (SSE)로 LLM 답변 실시간 스트리밍
- 상태 업데이트 메시지 전송 (분류 중, 검색 중, 답변 생성 중)
- Evidence 메타데이터 별도 전송
- 에러 핸들링 및 캐시 미스 자동 복구

### 5. 근거 기반 답변 (Citation)
**인용 형식**:
- `[정책문서 X]`: 정책 상세 페이지 링크
- `[웹 X]`: 웹 검색 결과 URL

**Evidence 제공**:
```json
{
  "type": "policy" | "web",
  "content": "...",
  "metadata": {
    "policy_id": 123,
    "title": "...",
    "url": "...",
    "score": 0.95
  }
}
```

## 🎯 성능 최적화

### 캐싱 전략
- **정책 문서 캐싱**: 세션당 1회 Qdrant 조회 후 메모리 캐싱
- **대화 히스토리 캐싱**: 멀티턴 대화 컨텍스트 유지
- **TTL 관리**: 브라우저 닫기 시 자동 정리

### 검색 성능
- **Hybrid Search**: Dense + Sparse로 정확도 향상
- **RRF**: 두 검색 결과의 가중 평균으로 최적화
- **동적 임계값**: 결과 수에 따라 threshold 자동 조정

### 응답 속도
- **SSE 스트리밍**: 첫 토큰 응답 시간 최소화
- **병렬 처리**: 웹 검색과 LLM 호출 최적화
- **LangSmith 트레이싱**: 병목 구간 실시간 모니터링

## 📚 추가 문서
- 프로젝트 내 `.md` 파일들은 개발 중 작성된 설계 문서로, Git에서 제외됨
- 최신 정보는 본 `README.md`를 참고하세요



