# 정책·지원금 AI Agent (Policy & Grant AI Assistant)

## 📋 프로젝트 개요

정부 정책·지원금 정보를 쉽게 탐색하고, **근거 기반 설명 + 자격 가능성 판단**까지 제공하는 AI 에이전트 웹 서비스입니다.

### 주요 기능
- 🔍 **빠른 정책 검색**: 하이브리드 검색 (Dense 벡터 + Sparse BM25) 기반 초고속 검색
- 💬 **Q&A 멀티턴**: 특정 정책에 대한 상세 질의응답 (LangGraph 워크플로우)
- ✅ **자격 확인**: 체크리스트 기반 자격 조건 판정
- 📊 **근거 제공**: 모든 답변에 출처 명시
- 🌐 **웹검색 보강**: DB 부족 시 실시간 웹검색 (Tavily)

## 🚀 핵심 특징

### ⚡ 초고속 검색 시스템
- **LLM 호출 제거**: 검색 단계에서 LLM을 사용하지 않아 평균 응답 시간 **0.5-2초** (기존 5-10초 대비 **80% 개선**)
- **하이브리드 검색**: Dense 벡터 검색 + Sparse BM25 키워드 검색 결합으로 검색 품질 향상
- **동적 유사도 조정**: 키워드와 결과 수에 따라 자동으로 임계값 조정
- **검색 품질 지표**: 상세한 메트릭스 및 근거 제공

### 🎯 하이브리드 검색 (Hybrid Search)
- **Dense 검색**: BGE-M3 임베딩 기반 의미적 유사성 검색 (Qdrant)
- **Sparse 검색**: BM25 알고리즘 기반 키워드 매칭 검색
- **RRF 결합**: Reciprocal Rank Fusion으로 두 검색 결과 통합
- **자동 인덱스 구축**: 첫 검색 시 Qdrant 문서로부터 BM25 인덱스 자동 생성

## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI, Python 3.11
- **Workflow**: LangGraph (Q&A, 자격확인용)
- **DB**: MySQL 8.0, Qdrant (Vector DB)
- **LLM**: OpenAI API (Q&A, 자격확인용)
- **Embedding**: bge-m3 (BAAI/bge-m3, 1024차원)
- **검색**: 하이브리드 검색 (Dense + Sparse BM25)
- **웹 검색**: Tavily API
- **Observability**: LangSmith

### Frontend
- **Framework**: Next.js 14 (App Router)
- **State**: Zustand
- **Style**: Tailwind CSS
- **TypeScript**: 완전한 타입 안정성

### Infrastructure
- **Backend**: Docker + Cloudtype
- **Frontend**: Vercel
- **Monitoring**: LangSmith

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 레포지토리 클론
git clone <repository-url>

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

# 검색 API 테스트
curl "http://localhost:8000/api/v1/policies/search?query=창업"

# API 문서 확인
open http://localhost:8000/docs
```

### 5. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
# 브라우저에서 http://localhost:3000 접속
```

## 📁 프로젝트 구조

```
policy_agent_searchspark/
├── README.md                             # 프로젝트 개요 및 가이드
├── .env.example                          # 환경변수 템플릿
├── docker-compose.yml                    # Docker Compose 설정
├── data.json                             # 정책 데이터 (MySQL/Qdrant 적재용)
│
├── infra/                                # 인프라 설정
│   └── mysql/
│       ├── init/
│       │   └── 001_init.sql             # 데이터베이스 스키마
│       └── my.cnf                        # MySQL 설정
│
├── backend/                               # FastAPI 백엔드
│   ├── requirements.txt                   # Python 패키지
│   ├── pytest.ini                         # Pytest 설정
│   ├── scripts/
│   │   └── ingest_data.py                # 데이터 적재 스크립트
│   └── src/app/
│       ├── main.py                       # FastAPI 앱 생성
│       │
│       ├── api/                          # API 라우터
│       │   ├── routes_policy.py         # 정책 검색 API
│       │   ├── routes_chat.py           # Q&A API
│       │   ├── routes_eligibility.py    # 자격확인 API
│       │   ├── routes_web_source.py     # 웹 근거 API
│       │   └── routes_admin.py          # 관리자 API
│       │
│       ├── services/                     # 비즈니스 로직
│       │   ├── simple_search_service.py # 빠른 검색 서비스 (NEW)
│       │   ├── search_config.py         # 검색 설정 (NEW)
│       │   ├── policy_search_service.py # 기존 검색 서비스
│       │   └── web_source_service.py    # 웹 검색 서비스
│       │
│       ├── vector_store/                 # 벡터 검색
│       │   ├── qdrant_client.py         # Qdrant 클라이언트
│       │   ├── embedder_bge_m3.py       # BGE-M3 임베딩
│       │   ├── sparse_search.py         # BM25 검색 (NEW)
│       │   └── chunker.py               # 텍스트 청킹
│       │
│       ├── agent/                        # LangGraph 워크플로우
│       │   ├── controller.py            # 에이전트 컨트롤러
│       │   ├── nodes/                   # 워크플로우 노드
│       │   └── workflows/               # 워크플로우 정의
│       │
│       ├── db/                           # 데이터베이스
│       │   ├── engine.py                # SQLAlchemy 엔진
│       │   ├── models.py                # ORM 모델
│       │   └── repositories/            # Repository 패턴
│       │
│       ├── web_search/                   # 웹 검색
│       │   └── clients/
│       │       └── tavily_client.py     # Tavily 클라이언트
│       │
│       └── config/                       # 설정
│           ├── settings.py              # 환경변수 설정
│           └── logger.py               # 로깅 설정
│
└── frontend/                             # Next.js 프론트엔드
    ├── package.json
    ├── next.config.js
    └── src/
        ├── app/                          # Next.js App Router
        │   ├── page.tsx                 # 홈 페이지
        │   ├── search/page.tsx          # 검색 결과 페이지
        │   └── policy/[policyId]/       # 정책 상세 페이지
        ├── components/                   # React 컴포넌트
        ├── lib/                          # 유틸리티
        │   ├── api.ts                   # API 클라이언트
        │   └── types.ts                 # TypeScript 타입
        └── store/                        # Zustand 상태 관리
```

## 🔍 검색 시스템 아키텍처

### SimpleSearchService

기존 LangGraph 기반 Search Agent 워크플로우를 대체하는 **빠르고 효율적인 검색 서비스**입니다.

#### 주요 특징
- ✅ **LLM 호출 제거**: 검색 단계에서 LLM을 사용하지 않음
- ✅ **하이브리드 검색**: Dense 벡터 + Sparse BM25 결합
- ✅ **동적 임계값 조정**: 키워드와 결과 수에 따라 자동 조정
- ✅ **검색 품질 지표**: 상세한 메트릭스 제공

#### 검색 흐름

```
사용자 쿼리
    ↓
[키워드 추출] ← 규칙 기반 (빠름)
    ↓
┌─────────────────────────────────┐
│      하이브리드 검색 (병렬)        │
├─────────────┬───────────────────┤
│ Dense 검색   │   Sparse 검색     │
│ (Qdrant)    │   (BM25)         │
│ BGE-M3      │   키워드 매칭     │
└─────────────┴───────────────────┘
    ↓
[RRF 결합] ← Reciprocal Rank Fusion
    ↓
[MySQL 메타데이터 조회]
    ↓
[충분성 검사] ← 규칙 기반 판단
    ↓
[웹 검색] ← Tavily (조건부)
    ↓
결과 반환 (0.5-2초)
```

### 하이브리드 검색 상세

#### Dense 검색 (벡터 검색)
- **모델**: BGE-M3 (BAAI/bge-m3)
- **차원**: 1024차원
- **저장소**: Qdrant
- **특징**: 의미적 유사성 기반 검색

#### Sparse 검색 (BM25)
- **알고리즘**: BM25 (Best Matching 25)
- **토크나이저**: 한국어 규칙 기반 토크나이저
- **인덱스**: 자동 구축 (첫 검색 시)
- **특징**: 키워드 매칭 기반 검색

#### RRF 결합 (Reciprocal Rank Fusion)
```python
RRF_score = sum(1 / (k + rank_i))
```
- 두 검색 방법의 순위를 기반으로 최종 점수 계산
- `k` 파라미터: 60 (기본값)
- 두 방법에서 모두 높은 순위를 받은 문서가 상위에 위치

### 동적 유사도 임계값 조정

검색 결과 수와 키워드에 따라 자동으로 임계값을 조정합니다.

```python
# 키워드별 조정
keyword_adjustments = {
    "지원금": -0.05,  # 더 많은 결과
    "창업": -0.05,
    "R&D": 0.05,     # 더 정확한 결과
}

# 결과 수 기반 조정
if result_count < 3:
    threshold -= 0.05  # 결과 부족 시 임계값 낮춤
elif result_count > 15:
    threshold += 0.03  # 결과 과다 시 임계값 높임
```

## 🔍 API 엔드포인트

### 검색 API (새로운 빠른 검색)

#### `GET /api/v1/policies/search`

빠른 정책 검색 API (LLM 호출 없음)

**요청 파라미터:**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `query` | string | ✓ | 검색 쿼리 |
| `region` | string | | 지역 필터 |
| `category` | string | | 카테고리 필터 |
| `target_group` | string | | 대상 그룹 필터 |
| `session_id` | string | | 세션 ID (선택) |

**응답 구조:**
```json
{
  "session_id": "string",
  "summary": "검색 결과 요약",
  "policies": [
    {
      "id": 1,
      "program_name": "정책명",
      "region": "서울",
      "category": "사업화",
      "score": 0.85,
      "source_type": "internal"
    }
  ],
  "total_count": 10,
  "top_score": 0.85,
  "is_sufficient": true,
  "sufficiency_reason": "충분한 결과를 찾았습니다",
  "web_sources": [],
  "metrics": {
    "total_candidates": 100,
    "final_count": 10,
    "top_score": 0.85,
    "avg_score": 0.72,
    "score_threshold_used": 0.25,
    "web_search_triggered": false,
    "search_time_ms": 500
  },
  "evidence": [
    {
      "policy_id": 1,
      "matched_content": "매칭된 텍스트",
      "score": 0.85,
      "match_type": "hybrid"
    }
  ]
}
```

**예시:**
```bash
# 기본 검색
curl "http://localhost:8000/api/v1/policies/search?query=창업"

# 필터 적용
curl "http://localhost:8000/api/v1/policies/search?query=창업&region=서울&category=사업화"
```

### 기존 API

#### Policies
- `GET /api/v1/policies`: 정책 목록 조회 (레거시)
- `GET /api/v1/policies/{id}`: 정책 상세 조회
- `GET /api/v1/policies/regions`: 지역 목록
- `GET /api/v1/policies/categories`: 카테고리 목록

#### Chat
- `POST /api/v1/chat`: Q&A 멀티턴 대화
- `POST /api/v1/session/reset`: 세션 초기화

#### Eligibility
- `POST /api/v1/eligibility/start`: 자격 확인 시작
- `POST /api/v1/eligibility/answer`: 자격 확인 답변
- `GET /api/v1/eligibility/result/{session_id}`: 결과 조회

#### Admin
- `GET /health`: 헬스체크
- `GET /api/v1/admin/stats`: 서비스 통계

## ⚙️ 검색 설정

검색 동작을 커스터마이징할 수 있습니다.

### 기본 설정 (search_config.py)

```python
# 기본 유사도 임계값
default_score_threshold: float = 0.25  # 낮을수록 더 많은 결과

# 목표 결과 수
target_min_results: int = 3
target_max_results: int = 15

# 하이브리드 검색 가중치
dense_weight: float = 0.7   # Dense 검색 가중치
sparse_weight: float = 0.3   # Sparse 검색 가중치

# 웹 검색 트리거
web_search_trigger_count: int = 2      # 결과가 2개 미만이면 웹 검색
web_search_trigger_score: float = 0.35 # 최고 점수가 0.35 미만이면 웹 검색
```

### 런타임 설정 변경

```python
from app.services import update_search_config

# 임계값 조정
update_search_config(default_score_threshold=0.30)

# 하이브리드 가중치 조정
update_search_config(
    dense_weight=0.6,
    sparse_weight=0.4
)

# 검색 모드 변경
from app.services.search_config import SearchMode
update_search_config(search_mode=SearchMode.DENSE)  # 벡터 검색만
```

## 📊 성능 비교

| 지표 | 이전 (Search Agent) | 이후 (SimpleSearch) | 개선율 |
|------|---------------------|---------------------|--------|
| 평균 응답 시간 | 5-10초 | 0.5-2초 | **80%↓** |
| LLM API 호출 | 3회/검색 | 0회/검색 | **100%↓** |
| 검색 품질 | 높음 | 높음 (하이브리드) | 유지 |
| 비용 | 높음 | 낮음 | **대폭 절감** |

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
# 브라우저에서 http://localhost:3000 접속
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
- **포인트 수**: 약 13,000개 (정책당 평균 20-30개 청크)

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

# 컨테이너 중지
docker-compose stop

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
docker exec -it policy_mysql mysql -u policy_user -ppolicypass123 policy_db

# 데이터 적재
docker exec -it policy_backend python scripts/ingest_data.py
```

### 데이터베이스 관리

```bash
# Adminer 접속 (MySQL GUI)
# 브라우저에서 http://localhost:8080 접속
# 서버: mysql
# 사용자: policy_user
# 비밀번호: policypass123
# 데이터베이스: policy_db

# Qdrant 대시보드 접속
# 브라우저에서 http://localhost:6335/dashboard 접속
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
DATABASE_URL=mysql+pymysql://policy_user:policypass123@mysql:3306/policy_db

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=policies

# OpenAI (Q&A, 자격확인용)
OPENAI_API_KEY=sk-...

# Tavily (웹 검색용)
TAVILY_API_KEY=tvly-...

# LangSmith (옵션)
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=policy-qa-agent
LANGSMITH_TRACING=true

# App
APP_NAME=Policy Q&A Agent
ENVIRONMENT=development
DEBUG=true
```

## 🎯 검색 시스템 상세 설명

### 검색 모드

#### 1. Dense 검색 (벡터 검색)
- **방식**: 쿼리를 벡터로 변환 후 Qdrant에서 유사 문서 검색
- **장점**: 의미적 유사성 포착
- **단점**: 정확한 키워드 매칭 어려움

#### 2. Sparse 검색 (BM25)
- **방식**: 쿼리 토큰화 후 BM25 알고리즘으로 키워드 매칭
- **장점**: 정확한 키워드 매칭
- **단점**: 동의어/유의어 처리 어려움

#### 3. Hybrid 검색 (권장)
- **방식**: Dense + Sparse 검색 결과를 RRF로 결합
- **장점**: 두 방법의 장점 결합
- **결과**: 더 높은 검색 품질

### 매칭 타입

검색 결과의 `match_type` 필드로 어떤 방식으로 매칭되었는지 확인:

| match_type | 설명 |
|------------|------|
| `dense` | Dense 검색에서만 매칭 |
| `sparse` | Sparse 검색에서만 매칭 |
| `hybrid` | 두 검색 모두에서 매칭 (가장 신뢰도 높음) |

### 웹 검색 트리거 조건

웹 검색은 다음 조건 중 하나라도 만족할 때 실행됩니다:

1. **결과 수 부족**: `result_count < 2` (기본값)
2. **낮은 유사도**: `top_score < 0.35` (기본값)

## 📈 LangSmith 모니터링

### 트레이싱 태그
- `env:development|production`: 환경
- `feature:SEARCH|Q&A|Eligibility-Check`: 기능
- `policy:{policy_id}`: 정책 ID
- `session:{session_id}`: 세션 ID

### 평가 메트릭
- **Groundedness**: 근거 기반성 (≥ 0.9 목표)
- **Citation Rate**: 인용률 (≥ 0.95 목표)
- **Response Time**: 응답 시간 (< 3초 목표)

## 🚀 배포

### Backend (Cloudtype)

```bash
# Docker 이미지 빌드
docker build -t policy-backend:latest -f infra/cloudtype/backend.Dockerfile .

# Cloudtype에 배포
# (Cloudtype 대시보드에서 설정)
```

### Frontend (Vercel)

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
cd frontend
vercel
```

## 📚 추가 문서

- [검색 시스템 개선 문서](./backend/src/app/services/README.md) (예정)
- [API 문서](http://localhost:8000/docs) (로컬 실행 시)

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 👥 팀

- 개발: 권문진, 고민서, 권효주

---

**Made with ❤️ by Policy Agent Team**
