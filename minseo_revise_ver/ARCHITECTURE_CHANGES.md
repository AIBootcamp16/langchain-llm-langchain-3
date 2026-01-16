# 🏗️ 아키텍처 변경 사항 (Architecture Changes)

## 📋 개요

이 문서는 **MVP 코드 (`langchain-llm-langchain-3-mvp`)**와 **현재 프로젝트** 간의 차이점을 상세하게 설명합니다.

**MVP 코드 기준점**: `langchain-llm-langchain-3-mvp/` 디렉토리  
**현재 프로젝트**: 메인 프로젝트 루트의 모든 파일

---

## 📊 MVP vs 현재 프로젝트 비교 요약

| 구분 | MVP 코드 | 현재 프로젝트 |
|------|---------|-------------|
| **검색 시스템** | `PolicySearchService` (하이브리드 검색) | `SimpleSearchService` + `PolicySearchService` (하이브리드 검색) |
| **검색 워크플로우** | ❌ 없음 | ✅ `search_workflow.py` (LangGraph, 현재 비활성화) |
| **LLM 클라이언트** | OpenAI만 | OpenAI + Solar (Upstage) |
| **검색 노드** | ❌ 없음 | ✅ `agent/nodes/search/` 디렉토리 (5개 노드) |
| **Sparse 검색** | ❌ 없음 | ✅ `sparse_search.py` (BM25) |
| **검색 설정** | ❌ 없음 | ✅ `search_config.py` (동적 유사도 조정) |
| **검색 API** | `/api/v1/policies` (기본 검색) | `/api/v1/policies/search` (빠른 검색) + 기본 검색 |
| **프론트엔드 검색** | `getPolicies()` | `searchPolicies()` (새로운 API) + `getPolicies()` |

---

## 🔄 주요 변경사항 요약

### 이전 아키텍처 → 새로운 아키텍처

| 구분 | 이전 (LangGraph Workflow) | 새로운 (SimpleSearchService) |
|------|---------------------------|------------------------------|
| **검색 방식** | LangGraph StateGraph 기반 다단계 워크플로우 | 단순 함수 기반 검색 서비스 |
| **LLM 호출** | ✅ 사용 (query_understanding, check_sufficiency) | ❌ 미사용 (빠른 검색) |
| **검색 알고리즘** | Dense 벡터 검색 (Qdrant) | 하이브리드 검색 (Dense + Sparse BM25) |
| **결과 결합** | - | RRF (Reciprocal Rank Fusion) |
| **유사도 임계값** | 고정값 | 동적 조정 (결과 수에 따라) |
| **성능** | 느림 (LLM 호출) | 빠름 (벡터 검색만) |
| **응답 시간** | 수 초 ~ 수십 초 | 수백 밀리초 |

---

## 📁 변경된 파일 목록 (MVP 대비)

### 🆕 새로 추가된 파일

#### 1. `backend/src/app/services/simple_search_service.py`
**MVP 상태**: ❌ 없음  
**현재 상태**: ✅ 추가됨
- **목적**: LLM 호출 없이 빠른 정책 검색 서비스
- **주요 기능**:
  - 하이브리드 검색 (Dense + Sparse BM25)
  - RRF (Reciprocal Rank Fusion) 기반 결과 결합
  - 동적 유사도 임계값 조정
  - 웹 검색 폴백 (Tavily)
  - 검색 품질 지표 계산
- **클래스**: `SimpleSearchService`, `SearchMetrics`

#### 2. `backend/src/app/services/search_config.py`
**MVP 상태**: ❌ 없음  
**현재 상태**: ✅ 추가됨
- **목적**: 검색 설정 및 동적 유사도 조정 로직
- **주요 기능**:
  - 검색 모드 설정 (Dense, Sparse, Hybrid)
  - 동적 유사도 임계값 계산
  - 키워드별/지역별/카테고리별 유사도 조정
  - 웹 검색 트리거 조건 설정
- **클래스**: `SearchConfig`, `SimilarityStrategy`, `SearchMode`

#### 3. `backend/src/app/vector_store/sparse_search.py`
**MVP 상태**: ❌ 없음  
**현재 상태**: ✅ 추가됨
- **목적**: BM25 기반 희소 벡터 검색 (키워드 기반)
- **주요 기능**:
  - 한국어 토크나이저 (`KoreanTokenizer`)
  - BM25 인덱스 구축 및 검색 (`BM25Index`)
  - 하이브리드 검색기 (`HybridSearcher`) - Dense + Sparse 결합
  - RRF (Reciprocal Rank Fusion) 지원
- **클래스**: `BM25Index`, `HybridSearcher`, `KoreanTokenizer`

#### 4. `backend/src/app/llm/solar_client.py`
**MVP 상태**: ❌ 없음  
**현재 상태**: ✅ 추가됨
- **목적**: Solar (Upstage) LLM 클라이언트
- **주요 기능**:
  - `langchain-upstage`의 `ChatUpstage` 래핑
  - 메시지 기반 응답 생성
  - LangSmith 추적 지원
- **클래스**: `SolarClient`

#### 5. `backend/src/app/agent/workflows/search_workflow.py`
**MVP 상태**: ❌ 없음  
**현재 상태**: ✅ 추가됨 (현재는 비활성화됨)
- **목적**: LangGraph 기반 검색 워크플로우
- **주요 기능**:
  - `query_understanding_node`: 쿼리 이해 (LLM)
  - `search_retrieve_node`: 벡터 검색
  - `search_check_sufficiency_node`: 충분성 검사
  - `search_web_search_node`: 웹 검색
  - `summarize_node`: 결과 요약
- **상태**: 현재는 `SimpleSearchService`로 대체되어 사용하지 않음

#### 6. `backend/src/app/agent/nodes/search/` 디렉토리 (전체)
**MVP 상태**: ❌ 없음  
**현재 상태**: ✅ 추가됨
- **파일 목록**:
  - `query_understanding_node.py`: 쿼리 이해 노드 (LLM)
  - `search_check_node.py`: 충분성 검사 노드
  - `search_retrieve_node.py`: 벡터 검색 노드
  - `search_web_node.py`: 웹 검색 노드
  - `summarize_node.py`: 결과 요약 노드
- **상태**: `search_workflow.py`와 함께 현재는 사용하지 않음

---

### ✏️ 수정된 파일

#### 7. `backend/src/app/agent/controller.py`
**MVP 상태**: `run_qa()`, `reset_session()` 메서드만 존재  
**현재 상태**: `run_search()` 메서드 추가
**변경 내용**:
- ❌ 제거: `create_search_workflow()` import 및 `_search_app` 인스턴스
- ✅ 추가: `run_search()` 메서드가 `SimpleSearchService` 사용하도록 변경
- **이전**: LangGraph 워크플로우 실행 (`_search_app.invoke()`)
- **이후**: `SimpleSearchService.search()` 직접 호출

```python
# 이전 (주석 처리됨)
# from .workflows.search_workflow import create_search_workflow
# _search_app = create_search_workflow()

# 이후
from ..services import get_simple_search_service
search_service = get_simple_search_service()
result = search_service.search(...)
```

#### 8. `backend/src/app/api/routes_policy.py`
**MVP 상태**: 
- `/api/v1/policies` (기본 검색)
- `/api/v1/policy/{policy_id}` (상세 조회)
- `/api/v1/policies/regions` (지역 목록)
- `/api/v1/policies/categories` (카테고리 목록)

**현재 상태**: 
- ✅ `/api/v1/policies/search` 엔드포인트 추가 (빠른 검색)
- ✅ `SearchAgentResponse` 등 새로운 Pydantic 모델 추가
- ✅ 라우트 순서 조정 (422 에러 방지)
- ✅ `SearchAgentPolicyResponse.from_dict()` 메서드 추가 (리스트→문자열 변환)

**변경 내용**:
- ✅ 추가: `/api/v1/policies/search` 엔드포인트 (새로운 빠른 검색 API)
- ✅ 추가: `/api/v1/policies/regions` 엔드포인트 (지역 목록 조회)
- ✅ 추가: `/api/v1/policies/categories` 엔드포인트 (카테고리 목록 조회)
- ✅ 추가: `SearchAgentPolicyResponse.from_dict()` 클래스 메서드 (리스트→문자열 변환)
- 🔧 수정: 라우트 순서 조정 (특정 경로를 `/regions`, `/categories`보다 앞에 배치하여 422 에러 방지)
- **주요 Pydantic 모델**: `SearchAgentResponse`, `SearchMetricsResponse`, `SearchEvidenceResponse`

**API 엔드포인트 변경**:
```python
# 새로운 검색 엔드포인트
GET /api/v1/policies/search?query=창업&region=서울

# 필터 엔드포인트 (추가)
GET /api/v1/policies/regions
GET /api/v1/policies/categories
```

#### 9. `backend/src/app/services/policy_search_service.py`
**MVP 상태**: 하이브리드 검색 (Qdrant + MySQL + 웹 검색)  
**현재 상태**: 동일하지만 `SimpleSearchService`와 함께 사용
**변경 내용**:
- 기본 구조는 동일하지만, 새로운 검색 엔드포인트에서는 `SimpleSearchService` 사용
- 기존 엔드포인트는 여전히 `PolicySearchService` 사용 (호환성 유지)

#### 10. `backend/src/app/config/settings.py`
**MVP 상태**: 
- OpenAI만 지원
- CORS origins: `["http://localhost:3000", "http://localhost:3001"]`
- `.env` 파일 경로: 상대 경로

**현재 상태**: 
- ✅ Solar (Upstage) LLM 지원 추가
- ✅ `llm_provider` 설정 추가 (기본값: "solar")
- ✅ CORS origins 확장: `localhost:3000~3005`
- ✅ `.env` 파일 경로: 절대 경로로 변경 (`Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"`)
- ✅ `solar_api_key`, `solar_model`, `solar_temperature` 설정 추가
- ✅ `UPSTAGE_API_KEY` 별칭 지원

**변경 내용**:
```python
# MVP
openai_api_key: str  # 필수
# Solar 관련 설정 없음

# 현재
llm_provider: str = "solar"  # 기본값
openai_api_key: Optional[str] = None  # 선택적
solar_api_key: Optional[str] = Field(
    default=None,
    validation_alias=AliasChoices("SOLAR_API_KEY", "UPSTAGE_API_KEY"),
)
```

#### 11. `frontend/src/lib/api.ts`
**MVP 상태**: 
- `getPolicies()`: `/api/v1/policies` 호출
- `getPolicy()`: `/api/v1/policy/{id}` 호출 (단수)
- `getRegions()`, `getCategories()`: 존재

**현재 상태**: 
- ✅ `searchPolicies()` 함수 추가: `/api/v1/policies/search` 호출
- ✅ `getPolicy()` 수정: `/api/v1/policies/{id}` 호출 (복수)
- ✅ `getRegions()`, `getCategories()` 유지

**변경 내용**:
- ✅ 추가: `searchPolicies()` 함수 (새로운 빠른 검색 API 호출)
- ✅ 추가: `getRegions()`, `getCategories()` 함수
- 🔧 수정: `getPolicy()` 함수의 엔드포인트 경로 (`/api/v1/policy/{id}` → `/api/v1/policies/{id}`)
- **타입**: `SearchResponse` 타입 추가

#### 12. `frontend/src/lib/types.ts`
**MVP 상태**: 
- `Policy` 인터페이스: 필수 필드만 (nullable 없음)
- `SearchParams` 인터페이스: `target_group` 없음
- `SearchResponse` 인터페이스: 없음

**현재 상태**: 
- ✅ `Policy` 인터페이스: 많은 필드를 `Optional<type | null>`로 변경
- ✅ `source_type?: string` 필드 추가 (웹 검색 결과 구분용)
- ✅ `SearchResponse` 인터페이스 추가 (검색 결과 타입)
- ✅ `SearchParams`에 `target_group?: string` 추가
- ✅ `SearchMetrics`, `SearchEvidence`, `WebSource`, `ParsedQuery` 인터페이스 추가

**변경 내용**:
- ✅ 추가: `SearchResponse` 인터페이스 (검색 결과 타입)
- 🔧 수정: `Policy` 인터페이스 필드를 `Optional<type | null>`로 변경
  - `program_id`, `region`, `category`, `support_description`, `support_budget`, `apply_target`, `announcement_date`, `application_method`, `contact_agency`, `created_at`, `updated_at`
- ✅ 추가: `source_type?: string` 필드 (웹 검색 결과 구분용)
- ✅ 추가: `original_query?: string` (SearchResponse)

#### 13. `frontend/src/app/search/page.tsx`
**MVP 상태**: 
- `getPolicies()` API 사용
- 로딩 메시지: "AI가 사업자 등록 정보를 바탕으로 최적의 보조금을 분석하고 있습니다."
- 진행률: 10%씩 증가, 200ms 간격

**현재 상태**: 
- ✅ `searchPolicies()` API 사용 (새로운 빠른 검색)
- ✅ 로딩 메시지: "LLM 호출 없이 빠르게 검색합니다"
- ✅ 진행률: 15%씩 증가, 100ms 간격 (더 빠름)
- ✅ 디버깅용 `console.log` 추가
- ✅ `setSearchResult()` 사용 (Zustand store)

**변경 내용**:
- ✅ 추가: `searchPolicies()` API 호출 로직
- ❌ 제거: 검색 품질 지표 UI (최고 유사도, 평균 유사도, 웹 검색 포함, 임계값, 검색 소요 시간)
- ✅ 추가: 디버깅용 `console.log` 문 (나중에 제거 가능)
- **상태 관리**: Zustand `usePolicyStore` 사용

#### 14. `frontend/src/components/policy/PolicyList.tsx`
**MVP 상태**: 
- `PolicyCard` 컴포넌트 사용
- 기본적인 정책 정보 표시

**현재 상태**: 
- ✅ `source_type === 'web'`인 경우 "웹 검색" 배지 표시
- ✅ `policy.url`이 있을 경우 "출처 링크" 클릭 가능한 링크 추가
- ✅ `null` 값 처리 개선 (`policy.region`, `policy.category`)
- ✅ 인라인 스타일로 간소화 (PolicyCard 제거)

**변경 내용**:
- ❌ 제거: 개별 정책 카드에서 "적합도 X%" 점수 표시
- ✅ 추가: `source_type === 'web'`인 경우 "web search" 배지 표시
- ✅ 추가: `policy.url`이 있을 경우 "출처 링크" 클릭 가능한 링크 추가
- 🔧 수정: `null` 값 처리 (`policy.region`, `policy.category`)

#### 15. `frontend/src/store/usePolicyStore.ts`
**MVP 상태**: 기본적인 정책 상태 관리  
**현재 상태**: 
- ✅ `setSearchResult()` 액션 추가 (새로운 검색 결과 형식 지원)
- ✅ 디버깅용 `console.log` 문 추가
- ✅ `summary`, `topScore`, `metrics`, `searchTimeMs` 등 추가 상태 관리

**변경 내용**:

---

### 🔄 MVP에는 없지만 현재 프로젝트에 추가된 기능

#### 16. 하이브리드 검색 (Dense + Sparse)
**MVP**: Dense 벡터 검색만 사용  
**현재**: Dense + Sparse (BM25) 하이브리드 검색
- `sparse_search.py`를 통한 BM25 키워드 검색
- RRF (Reciprocal Rank Fusion) 또는 가중 평균으로 결과 결합

#### 17. 동적 유사도 임계값 조정
**MVP**: 고정 임계값 사용 (`score_threshold: float = 0.7`)  
**현재**: 동적 임계값 조정 (`search_config.py`)
- 결과 수에 따라 자동 조정
- 키워드별/지역별 가중치 적용

#### 18. 검색 품질 지표
**MVP**: 기본적인 검색 결과만 반환  
**현재**: 상세한 검색 품질 지표 제공
- 최고/평균/최소 유사도
- 검색 소요 시간
- 충분성 판단 사유
- 웹 검색 트리거 여부

#### 19. Solar LLM 지원
**MVP**: OpenAI만 지원  
**현재**: OpenAI + Solar (Upstage) 지원
- `solar_client.py`를 통한 Solar LLM 통합
- `llm_provider` 설정으로 선택 가능

### 🗑️ 삭제된 파일 (사용되지 않아 제거됨)

#### 20. `backend/src/app/agent/workflows/search_workflow.py` ❌ 삭제됨
- **삭제일**: 2026-01-15
- **이유**: `SimpleSearchService`로 완전 대체되어 사용되지 않음
- **이전 역할**: LangGraph 기반 Search Workflow 생성
- **대체**: `SimpleSearchService`로 완전 대체됨

**삭제된 주요 함수**:
- `create_search_workflow()`: LangGraph StateGraph 생성
- `should_web_search()`: 충분성 검사 후 웹 검색 라우팅
- `run_search_workflow()`: 워크플로우 실행 함수

#### 21. `backend/src/app/agent/nodes/search/` 디렉토리 전체 ❌ 삭제됨
- **삭제일**: 2026-01-15
- **이유**: `search_workflow.py`에서만 사용되었고, 해당 파일이 삭제됨
- **이전 역할**: LangGraph 워크플로우용 검색 노드들
- **대체**: `SimpleSearchService`로 대체됨

**삭제된 파일 목록**:
1. `query_understanding_node.py` - 쿼리 이해 노드 (LLM 사용)
2. `search_retrieve_node.py` - 벡터 검색 노드
3. `search_check_node.py` - 충분성 검사 노드 (LLM 사용)
4. `search_web_node.py` - 웹 검색 노드
5. `summarize_node.py` - 결과 요약 노드 (LLM 사용)
6. `__init__.py` - 모듈 초기화 파일

**삭제 이유 요약**:
- 검색 기능이 LLM 호출 없이 빠른 벡터 검색으로 전환됨
- LangGraph 워크플로우 대신 단순 함수 기반 서비스 사용
- 성능 향상 및 비용 절감 (LLM 호출 제거)

---

### 🗑️ 사용되지 않는 파일 (삭제 가능)

현재 프로젝트에서 실제로 사용되지 않는 파일들입니다. 코드베이스를 정리하기 위해 삭제를 고려할 수 있습니다.

#### 22. 프롬프트 템플릿 파일 (검색 관련, LLM 미사용)

**`backend/src/app/prompts/policy_search_prompt.jinja2`**
- **이유**: 검색 기능은 `SimpleSearchService`를 사용하며 LLM 호출 없음
- **상태**: 어디서도 import되지 않음
- **확인**: `grep -r "policy_search_prompt"` 결과 없음

**`backend/src/app/prompts/policy_grading_prompt.jinja2`**
- **이유**: 검색 결과 등급 평가 기능이 제거됨
- **상태**: 어디서도 import되지 않음

**`backend/src/app/prompts/grading_prompt.jinja2`**
- **이유**: 검색 결과 등급 평가 기능이 제거됨
- **상태**: 어디서도 import되지 않음 (RAG_WORKFLOW_IMPROVEMENT.md에만 언급)

#### 23. 서비스 디렉토리의 프롬프트 파일 (중복/미사용)

**`backend/src/app/services/policy_grading_prompt.jinja2`**
- **이유**: `prompts/` 디렉토리에 동일한 파일이 있고, 어디서도 사용되지 않음
- **상태**: 어디서도 import되지 않음

**`backend/src/app/services/policy_search_prompt.jinja2`**
- **이유**: `prompts/` 디렉토리에 동일한 파일이 있고, 어디서도 사용되지 않음
- **상태**: 어디서도 import되지 않음

#### 24. 빈 파일

**`backend/src/app/services/template.py`**
- **이유**: 빈 파일 (내용 없음)
- **상태**: 어디서도 import되지 않음

#### 25. 문서 파일 (코드에서 참조되지 않음)

**`backend/src/app/services/RAG_WORKFLOW_IMPROVEMENT.md`**
- **이유**: 문서 파일이며, 코드에서 참조되지 않음
- **상태**: 문서만 존재, 코드에서 사용 안 함

**`backend/src/app/report.md`**
- **이유**: 문서 파일이며, 코드에서 참조되지 않음
- **상태**: 문서만 존재, 코드에서 사용 안 함

#### 26. 유틸리티 파일 (사용되지 않음)

**`backend/src/app/utils/template.py`**
- **이유**: `load_prompt()` 함수가 정의되어 있지만 실제로 사용되지 않음
- **상태**: `grep -r "load_prompt"` 결과 없음 (정의만 있고 사용 안 함)
- **참고**: 프롬프트는 직접 경로로 로드됨 (`answer_node.py` 참고)

**삭제 가능한 파일 요약**:
| 파일 경로 | 크기 (예상) | 삭제 이유 |
|---------|-----------|----------|
| `prompts/policy_search_prompt.jinja2` | ~1KB | 검색에서 LLM 미사용 |
| `prompts/policy_grading_prompt.jinja2` | ~1KB | 등급 평가 기능 제거 |
| `prompts/grading_prompt.jinja2` | ~1KB | 등급 평가 기능 제거 |
| `services/policy_grading_prompt.jinja2` | ~1KB | 중복, 미사용 |
| `services/policy_search_prompt.jinja2` | ~1KB | 중복, 미사용 |
| `services/template.py` | 0KB | 빈 파일 |
| `services/RAG_WORKFLOW_IMPROVEMENT.md` | ~10KB | 문서 파일 |
| `app/report.md` | ~5KB | 문서 파일 |
| `utils/template.py` | ~0.5KB | 미사용 함수 |

**총 예상 크기**: ~20KB


---

## 🚀 새로운 기능

### 1. 하이브리드 검색 (Hybrid Search)
- **Dense 검색**: Qdrant 벡터 검색 (의미 기반)
- **Sparse 검색**: BM25 키워드 검색 (텍스트 기반)
- **결합 방식**: RRF (Reciprocal Rank Fusion) 또는 가중 평균

```python
# 검색 모드 선택
SearchMode.DENSE   # 벡터 검색만
SearchMode.SPARSE  # 키워드 검색만
SearchMode.HYBRID  # 둘 다 결합 (기본값)
```

### 2. 동적 유사도 임계값 조정
- **고정값 → 적응형**: 결과 수에 따라 자동으로 임계값 조정
- **키워드별 가중치**: "창업", "지원금" 등 일반 키워드는 낮은 임계값
- **지역별 조정**: "전국" 검색 시 더 낮은 임계값 적용

```python
# 기본 임계값: 0.25
# 결과가 적으면: 임계값 자동 감소 (더 많은 결과)
# 결과가 많으면: 임계값 자동 증가 (더 정확한 결과)
```

### 3. 검색 품질 지표
- **지표 항목**:
  - 최고/평균/최소 유사도
  - 초기 후보 수, 필터링 후 결과 수
  - 웹 검색 트리거 여부
  - 검색 소요 시간
  - 충분성 판단 사유

### 4. 웹 검색 폴백
- **트리거 조건**:
  - 결과 수 < 2건
  - 최고 점수 < 0.35
- **동작**: Tavily API를 통한 웹 검색 수행 후 결과에 포함

### 5. 새로운 API 엔드포인트
- `GET /api/v1/policies/search`: 빠른 검색 API
- `GET /api/v1/policies/regions`: 지역 목록 조회
- `GET /api/v1/policies/categories`: 카테고리 목록 조회

---

## 📊 성능 개선

### 응답 시간
- **이전**: 5~30초 (LLM 호출 포함)
- **이후**: 100~500ms (벡터 검색만)

### 처리량
- **이전**: LLM 호출 제한으로 동시 처리 제한적
- **이후**: 벡터 검색만 사용하여 동시 처리 용이

### 비용
- **이전**: LLM 호출 비용 발생 (OpenAI/Solar)
- **이후**: LLM 호출 없음 (비용 절감)

---

## 🔧 설정 파일

### `backend/src/app/services/search_config.py`

검색 동작을 쉽게 조정할 수 있는 설정 파일입니다.

**주요 설정 항목**:
```python
# 기본 유사도 임계값
default_score_threshold: float = 0.25

# 목표 결과 수
target_min_results: int = 3
target_max_results: int = 15

# 웹 검색 트리거 조건
web_search_trigger_count: int = 2
web_search_trigger_score: float = 0.35

# 하이브리드 검색 가중치
dense_weight: float = 0.7
sparse_weight: float = 0.3
use_rrf: bool = True
```

---

## 🐛 해결된 이슈

### 1. Pydantic Validation Error
- **문제**: `contact_agency`, `application_method` 필드가 리스트로 전달됨
- **해결**: `SearchAgentPolicyResponse.from_dict()` 메서드에서 리스트→문자열 변환

### 2. FastAPI 422 Error
- **문제**: `/regions`, `/categories` 엔드포인트가 `/{policy_id}` 라우트에 의해 가로채짐
- **해결**: 라우트 순서 조정 (특정 경로를 동적 경로보다 앞에 배치)

### 3. 404 Error (Policy Detail)
- **문제**: 프론트엔드에서 `/api/v1/policy/{id}` 호출 (단수)
- **해결**: 백엔드 라우터 경로와 일치하도록 `/api/v1/policies/{id}` (복수)로 수정

### 4. 순환 Import
- **문제**: `create_search_workflow` import로 인한 순환 참조
- **해결**: `SimpleSearchService`로 대체하여 순환 참조 제거

---

## 📝 마이그레이션 가이드

### 기존 코드에서 새로운 API로 전환

**이전** (LangGraph Workflow):
```python
from app.agent.controller import AgentController

result = AgentController.run_search(...)  # 내부적으로 LangGraph 사용
```

**이후** (SimpleSearchService):
```python
from app.services import get_simple_search_service

search_service = get_simple_search_service()
result = search_service.search(...)  # 직접 서비스 호출
```

### 프론트엔드 API 호출

**이전**:
```typescript
// 레거시 엔드포인트
const response = await apiClient.get('/api/v1/policies', { params });
```

**이후**:
```typescript
// 새로운 빠른 검색 엔드포인트
const response = await searchPolicies({ query, region, category });
```

---

## 🎯 향후 계획

### 유지/개선 가능한 항목
1. ✅ **LangGraph Workflow 유지**: Q&A, Eligibility 체크 등은 여전히 LLM 기반 워크플로우 사용
2. 🔧 **검색 성능 튜닝**: RRF 파라미터, 가중치 조정
3. 📊 **검색 품질 모니터링**: 메트릭 수집 및 분석
4. 🌐 **웹 검색 개선**: Tavily 결과 후처리, 품질 필터링

### 제거/대체된 항목
1. ❌ **Search Workflow**: LangGraph 기반 검색 워크플로우는 더 이상 사용하지 않음
2. ❌ **LLM 기반 검색**: 쿼리 이해, 충분성 검사 등 LLM 노드 제거

---

## 📚 참고 문서

- [README.md](./README.md): 프로젝트 전체 개요 및 새로운 검색 시스템 설명
- [UNUSED_FILES.md](./UNUSED_FILES.md): 사용되지 않는 파일 목록 및 삭제 가이드
- [backend/src/app/services/simple_search_service.py](./backend/src/app/services/simple_search_service.py): SimpleSearchService 구현
- [backend/src/app/services/search_config.py](./backend/src/app/services/search_config.py): 검색 설정 파일

---

## 📅 변경 이력

- **2026-01-15**: 사용되지 않는 파일 정리 및 삭제
  - `backend/src/app/agent/workflows/search_workflow.py` 삭제
  - `backend/src/app/agent/nodes/search/` 디렉토리 전체 삭제 (6개 파일)
  - 사용되지 않는 파일 목록 정리 (`UNUSED_FILES.md` 생성)
- **2026-01-15**: MVP 코드와 현재 프로젝트 비교 문서 작성
- **2026-01-15**: SimpleSearchService 통합 완료
- **2026-01-15**: 프론트엔드 UI에서 기술 메트릭 제거 (사용자 친화적 UI)
- **2026-01-15**: `.gitignore` 파일 생성 (Git 저장소 준비)

---

## 📝 MVP 코드와의 주요 차이점 요약

### 백엔드 변경사항

1. **새로운 검색 서비스**
   - `SimpleSearchService`: LLM 호출 없이 빠른 검색
   - `search_config.py`: 동적 유사도 조정
   - `sparse_search.py`: BM25 기반 키워드 검색

2. **LLM 클라이언트 확장**
   - Solar (Upstage) LLM 지원 추가
   - `solar_client.py` 새로 추가

3. **검색 워크플로우**
   - `search_workflow.py` 및 관련 노드들 추가 (현재는 비활성화)
   - `agent/nodes/search/` 디렉토리 추가

4. **API 엔드포인트 확장**
   - `/api/v1/policies/search`: 새로운 빠른 검색 API
   - 기존 엔드포인트는 호환성 유지

### 프론트엔드 변경사항

1. **새로운 검색 API 사용**
   - `searchPolicies()` 함수 추가
   - `SearchResponse` 타입 추가

2. **타입 정의 확장**
   - `Policy` 인터페이스: nullable 필드 추가
   - `source_type` 필드 추가 (웹 검색 결과 구분)

3. **UI 개선**
   - 웹 검색 결과 배지 표시
   - 출처 링크 추가
   - 더 빠른 로딩 애니메이션

### 설정 변경사항

1. **환경 변수**
   - `SOLAR_API_KEY` 또는 `UPSTAGE_API_KEY` 추가
   - `LLM_PROVIDER` 설정 추가 (기본값: "solar")

2. **CORS 설정**
   - 더 많은 localhost 포트 지원 (3000~3005)

## 🤝 기여자

이 변경사항은 MVP 코드를 기반으로 하여 새로운 검색 시스템을 추가하고 개선한 결과입니다.

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-01-15
