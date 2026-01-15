# 검색 시스템 개선 문서

## 개요

기존 LangGraph 기반 Search Agent 워크플로우를 **SimpleSearchService**로 대체하여 검색 성능을 대폭 개선했습니다.

### 주요 변경 사항

1. **Search Agent 제거**: LLM 호출이 포함된 느린 워크플로우 제거
2. **하이브리드 검색 (Dense + Sparse)**: 벡터 검색과 BM25 키워드 검색 결합
3. **동적 유사도 임계값**: 키워드/결과 수에 따른 자동 임계값 조정
4. **검색 품질 지표**: 상세한 메트릭스 및 근거 제공
5. **Tavily 웹 검색 유지**: 결과 불충분 시 웹 검색 폴백

---

## 아키텍처 변경

### 이전 (Search Agent Workflow)

```
사용자 쿼리
    ↓
[query_understanding_node] ← LLM 호출 (느림)
    ↓
[search_retrieve_node] ← 벡터 검색
    ↓
[search_check_node] ← LLM 호출 (느림)
    ↓
[search_web_node] ← 웹 검색 (조건부)
    ↓
[search_generate_node] ← LLM 호출 (느림)
    ↓
결과 반환
```

**문제점:**
- 3회의 LLM 호출로 인한 지연 (평균 5-10초)
- 복잡한 워크플로우 구조
- 높은 API 비용

### 이후 (SimpleSearchService + Hybrid Search)

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
└─────────────┴───────────────────┘
    ↓
[RRF 결합] ← Reciprocal Rank Fusion
    ↓
[충분성 검사] ← 규칙 기반 판단
    ↓
[웹 검색] ← Tavily (조건부)
    ↓
결과 반환
```

**개선점:**
- LLM 호출 제거로 빠른 응답 (평균 0.5-2초)
- **하이브리드 검색**: 의미적 유사성(Dense) + 키워드 매칭(Sparse) 결합
- **RRF 결합**: 두 검색 결과의 순위 기반 통합
- 비용 절감

---

## 새로운 파일 구조

### Backend

```
backend/src/app/services/
├── __init__.py                    # 서비스 export
├── search_config.py               # 검색 설정 (NEW)
├── simple_search_service.py       # 간소화된 검색 서비스 (NEW)
└── policy_search_service.py       # 기존 서비스 (유지)

backend/src/app/vector_store/
├── qdrant_client.py               # Dense 검색 (Qdrant)
├── sparse_search.py               # Sparse 검색 (BM25) (NEW)
├── embedder_bge_m3.py             # 임베딩 모델
└── __init__.py                    # 모듈 export
```

### Frontend

```
frontend/src/
├── lib/
│   ├── api.ts                     # searchPolicies 함수 추가
│   └── types.ts                   # SearchResponse, SearchMetrics 타입 추가
├── store/
│   └── usePolicyStore.ts          # 검색 메트릭스 상태 추가
└── app/search/
    └── page.tsx                   # 메트릭스 표시 UI 추가
```

---

## 검색 설정 (SearchConfig)

### 위치
`backend/src/app/services/search_config.py`

### 주요 설정값

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `default_score_threshold` | 0.25 | 기본 유사도 임계값 |
| `min_score_threshold` | 0.15 | 최소 임계값 |
| `max_score_threshold` | 0.50 | 최대 임계값 |
| `qdrant_limit` | 100 | Qdrant 최대 후보 수 |
| `result_limit` | 50 | 최종 반환 결과 수 |
| `target_min_results` | 3 | 목표 최소 결과 수 |
| `target_max_results` | 15 | 목표 최대 결과 수 |
| `web_search_trigger_count` | 2 | 웹 검색 트리거 결과 수 |
| `web_search_trigger_score` | 0.35 | 웹 검색 트리거 점수 |

### 하이브리드 검색 설정

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `search_mode` | `HYBRID` | 검색 모드 (DENSE, SPARSE, HYBRID) |
| `dense_weight` | 0.7 | Dense 검색 가중치 |
| `sparse_weight` | 0.3 | Sparse 검색 가중치 |
| `use_rrf` | True | RRF 결합 사용 여부 |
| `rrf_k` | 60 | RRF k 파라미터 |
| `sparse_min_score` | 0.1 | Sparse 검색 최소 점수 |

### 키워드별 임계값 조정

특정 키워드에 따라 임계값이 자동으로 조정됩니다:

```python
keyword_threshold_adjustments = {
    # 일반적인 키워드 (임계값 낮춤 → 더 많은 결과)
    "지원금": -0.05,
    "보조금": -0.05,
    "지원사업": -0.05,
    "정책": -0.05,
    "창업": -0.05,
    "청년": -0.05,
    "중소기업": -0.05,
    "소상공인": -0.05,

    # 전문적인 키워드 (임계값 높임 → 정확한 결과)
    "R&D": 0.05,
    "수출": 0.05,
    "특허": 0.05,
}
```

### 동적 임계값 계산

```python
def calculate_threshold(
    self,
    keywords: List[str],
    region: Optional[str],
    category: Optional[str],
    current_result_count: int
) -> float:
    threshold = self.default_score_threshold

    # 1. 키워드 기반 조정
    for keyword in keywords:
        if keyword in self.keyword_threshold_adjustments:
            threshold += self.keyword_threshold_adjustments[keyword]

    # 2. 지역 필터 적용 시 임계값 낮춤
    if region:
        threshold -= 0.02

    # 3. 카테고리 필터 적용 시 임계값 낮춤
    if category:
        threshold -= 0.02

    # 4. 결과 수 기반 조정
    if current_result_count < self.target_min_results:
        threshold -= 0.05  # 결과 부족 시 임계값 낮춤
    elif current_result_count > self.target_max_results:
        threshold += 0.03  # 결과 과다 시 임계값 높임

    return max(self.min_score_threshold, min(self.max_score_threshold, threshold))
```

### 설정 변경 방법

```python
from app.services import get_search_config, update_search_config

# 현재 설정 조회
config = get_search_config()
print(f"현재 임계값: {config.default_score_threshold}")

# 설정 업데이트
update_search_config(
    default_score_threshold=0.30,
    web_search_trigger_count=3
)
```

---

## SimpleSearchService

### 위치
`backend/src/app/services/simple_search_service.py`

### 주요 메서드

#### `search()`

```python
def search(
    self,
    query: str,
    region: Optional[str] = None,
    category: Optional[str] = None,
    target_group: Optional[str] = None,
    session_id: Optional[str] = None,
    include_web_search: bool = True
) -> Dict[str, Any]:
    """
    정책 검색 수행

    Returns:
        {
            "session_id": str,
            "original_query": str,
            "summary": str,
            "policies": List[Policy],
            "total_count": int,
            "parsed_query": Dict,
            "top_score": float,
            "is_sufficient": bool,
            "sufficiency_reason": str,
            "web_sources": List[Dict],
            "metrics": SearchMetrics,
            "evidence": List[SearchEvidence],
            "error": Optional[str]
        }
    """
```

#### `_extract_keywords()`

규칙 기반 키워드 추출 (LLM 불필요):

```python
def _extract_keywords(self, query: str) -> Dict[str, Any]:
    """
    쿼리에서 키워드 추출

    - 한글 불용어 제거
    - 2글자 이상 단어만 추출
    - 지역/카테고리 자동 감지
    """
```

#### `_vector_search()`

Qdrant 벡터 검색 수행:

```python
def _vector_search(
    self,
    query: str,
    region: Optional[str],
    category: Optional[str],
    target_group: Optional[str],
    score_threshold: float
) -> Tuple[List[Policy], List[SearchEvidence]]:
    """
    벡터 DB 검색 및 MySQL 메타데이터 조회
    """
```

#### `_web_search()`

Tavily 웹 검색 (결과 불충분 시):

```python
def _web_search(
    self,
    query: str,
    keywords: List[str],
    region: Optional[str],
    target_group: Optional[str]
) -> List[Dict[str, Any]]:
    """
    Tavily API를 통한 웹 검색
    - 정부/공공기관 사이트 우선 검색
    - 최대 5개 결과 반환
    """
```

---

## API 변경 사항

### 엔드포인트

```
GET /api/v1/policies/search
```

### 요청 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `query` | string | ✓ | 검색 쿼리 |
| `region` | string | | 지역 필터 |
| `category` | string | | 카테고리 필터 |
| `target_group` | string | | 대상 그룹 필터 |

### 응답 구조

```typescript
interface SearchResponse {
  session_id: string;
  original_query: string;
  summary: string;
  policies: Policy[];
  total_count: number;
  parsed_query: {
    keywords: string[];
    region?: string;
    category?: string;
  };
  top_score: number;
  is_sufficient: boolean;
  sufficiency_reason: string;
  web_sources: WebSource[];
  metrics: SearchMetrics;
  evidence: SearchEvidence[];
  error?: string;
}

interface SearchMetrics {
  total_candidates: number;      // 전체 후보 수
  filtered_count: number;        // 필터링된 수
  final_count: number;           // 최종 결과 수
  top_score: number;             // 최고 유사도
  avg_score: number;             // 평균 유사도
  score_threshold_used: number;  // 사용된 임계값
  web_search_triggered: boolean; // 웹 검색 여부
  web_search_count: number;      // 웹 검색 결과 수
  search_time_ms: number;        // 검색 소요 시간 (ms)
}

interface SearchEvidence {
  policy_id: number;
  matched_content: string;  // 매칭된 내용
  score: float;             // 유사도 점수
  match_type: string;       // 매칭 타입 (vector_search, web_search)
}
```

---

## 프론트엔드 변경 사항

### 검색 API 호출

```typescript
// frontend/src/lib/api.ts
export const searchPolicies = async (params: SearchParams = {}): Promise<SearchResponse> => {
  const response = await apiClient.get<SearchResponse>('/api/v1/policies/search', { params });
  return response.data;
};
```

### 상태 관리

```typescript
// frontend/src/store/usePolicyStore.ts
interface PolicyState {
  // 기존 상태
  policies: Policy[];
  total: number;
  loading: boolean;

  // 새로운 검색 상태
  summary: string;
  topScore: number;
  isSufficient: boolean;
  sufficiencyReason: string;
  metrics: SearchMetrics | null;
  evidence: SearchEvidence[];
  searchTimeMs: number;
}
```

### UI 표시

검색 결과 화면에서 다음 정보를 표시합니다:

- 검색 소요 시간 (ms)
- 최고 유사도 점수
- 평균 유사도 점수
- 사용된 임계값
- 웹 검색 포함 여부

---

## 성능 비교

| 지표 | 이전 (Search Agent) | 이후 (SimpleSearch) | 개선율 |
|------|---------------------|---------------------|--------|
| 평균 응답 시간 | 5-10초 | 0.5-2초 | **80%↓** |
| LLM API 호출 | 3회/검색 | 0회/검색 | **100%↓** |
| 코드 복잡도 | 높음 (워크플로우) | 낮음 (단일 서비스) | - |
| 유지보수성 | 어려움 | 쉬움 | - |

---

## 웹 검색 트리거 조건

웹 검색은 다음 조건 중 하나라도 만족할 때 실행됩니다:

1. **결과 수 부족**: `result_count < web_search_trigger_count` (기본: 2개 미만)
2. **낮은 유사도**: `top_score < web_search_trigger_score` (기본: 0.35 미만)

```python
def should_trigger_web_search(self, result_count: int, top_score: float) -> bool:
    if result_count < self.web_search_trigger_count:
        return True
    if top_score < self.web_search_trigger_score:
        return True
    return False
```

---

## 하이브리드 검색 (Dense + Sparse)

### 개요

하이브리드 검색은 **Dense (벡터)** 검색과 **Sparse (BM25)** 검색을 결합하여 검색 품질을 향상시킵니다.

- **Dense 검색**: 의미적 유사성 기반 (BGE-M3 임베딩 + Qdrant)
- **Sparse 검색**: 키워드 매칭 기반 (BM25 알고리즘)

### 작동 방식

1. **Dense 검색**: 쿼리를 벡터로 변환 후 Qdrant에서 유사 문서 검색
2. **Sparse 검색**: 쿼리 토큰화 후 BM25 알고리즘으로 키워드 매칭
3. **결과 결합**: RRF (Reciprocal Rank Fusion)로 두 결과 통합

### RRF (Reciprocal Rank Fusion)

```python
RRF_score = sum(1 / (k + rank_i))
```

- 각 검색 방법의 순위를 기반으로 최종 점수 계산
- `k` 파라미터로 순위 차이의 영향 조절 (기본값: 60)
- 두 방법에서 모두 높은 순위를 받은 문서가 상위에 위치

### 매칭 타입

검색 결과의 `match_type` 필드로 어떤 방식으로 매칭되었는지 확인:

| match_type | 설명 |
|------------|------|
| `dense` | Dense 검색에서만 매칭 |
| `sparse` | Sparse 검색에서만 매칭 |
| `hybrid` | 두 검색 모두에서 매칭 (가장 신뢰도 높음) |

### BM25 인덱스

- **자동 구축**: 첫 검색 시 Qdrant 문서로부터 BM25 인덱스 자동 생성
- **한국어 토크나이저**: 불용어 제거 및 규칙 기반 토큰화
- **중요 키워드 가중치**: "지원금", "창업" 등 주요 키워드에 추가 가중치

### 설정 변경

```python
from app.services import update_search_config
from app.services.search_config import SearchMode

# 하이브리드 모드로 설정 (기본값)
update_search_config(search_mode=SearchMode.HYBRID)

# Dense 검색만 사용
update_search_config(search_mode=SearchMode.DENSE)

# 가중치 조정
update_search_config(
    dense_weight=0.6,
    sparse_weight=0.4
)
```

---

## 향후 개선 계획

1. ~~**하이브리드 검색**: Dense + Sparse 검색 조합~~ ✅ 완료
2. **검색 결과 캐싱**: Redis 기반 결과 캐싱
3. **사용자 피드백 반영**: 클릭률 기반 재순위화
4. **A/B 테스트**: 임계값 최적화를 위한 실험

---

## 참고 사항

- 기존 Search Agent 코드는 삭제되지 않고 주석 처리되어 있습니다
- 필요 시 `run_search_workflow` 함수를 다시 활성화할 수 있습니다
- 검색 설정은 서버 재시작 없이 런타임에 변경 가능합니다
