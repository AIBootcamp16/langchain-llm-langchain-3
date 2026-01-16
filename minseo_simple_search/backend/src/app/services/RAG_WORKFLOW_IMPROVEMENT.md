# 정책 검색 기능 고도화: LangGraph 기반 RAG 워크플로우 도입

## 1. 개요

기존의 단순 키워드 기반 검색 로직을 **LangGraph**를 활용한 지능형 RAG(Retrieval-Augmented Generation) 워크플로우로 전면 개편했습니다. 이를 통해 사용자 쿼리 의도를 더 정확하게 파악하고, 검색 결과가 부족할 경우 웹 검색을 통해 정보를 보강하며, 최종적으로 LLM이 가장 관련성 높은 순서로 결과를 재정렬하여 제공합니다. 모든 과정은 LangSmith를 통해 추적 및 관리가 가능합니다.

## 2. 정성적 개선 사항

- **지능적인 쿼리 이해**: 사용자의 자연어 쿼리("프리랜서를 위한 최신 정책")를 LLM이 분석하여 '카테고리 필터', '최신순 정렬' 등 구조화된 검색 조건으로 자동 변환합니다. 이로써 훨씬 더 정확한 맞춤 검색이 가능해졌습니다.
- **동적 정보 보강**: 내부 DB 검색 결과의 관련도가 설정된 임계값(유사도 0.65)보다 낮을 경우, 시스템이 자동으로 웹 검색(Tavily)을 수행하여 부족한 정보를 보충합니다. 이는 정보의 최신성과 포괄성을 크게 향상시킵니다.
- **결과 품질 향상 (LLM Grader)**: DB 검색 결과와 웹 검색 결과를 단순히 합치는 것이 아니라, LLM Grader가 사용자 쿼리와의 관련성을 기준으로 두 정보 소스를 종합적으로 평가하고 재정렬합니다. 이를 통해 사용자에게 가장 유용하고 관련성 높은 정보를 우선적으로 제시합니다.
- **워크플로우 관찰 가능성**: LangGraph와 LangSmith의 연동으로, 검색 요청이 어떤 과정을 거치는지(쿼리 이해 → DB 검색 → 웹 검색 → 최종 정렬) 각 단계별 성능(지연 시간, 비용 등)과 데이터를 시각적으로 추적하고 분석할 수 있게 되었습니다. 이는 향후 성능 튜닝 및 디버깅을 용이하게 합니다.

## 3. 정량적/기술적 변경 사항

### 3.1. 신규 파일

1.  **`backend/src/app/agent/workflows/search_workflow.py`**:
    *   정책 검색을 위한 전체 LangGraph 워크플로우를 정의합니다.
    *   `query_understanding`, `web_search`, `grade_policies` 노드와 `check_sufficiency` 조건부 엣지를 포함합니다.

2.  **`backend/src/app/prompts/policy_search_prompt.jinja2`**:
    *   `query_understanding` 노드에서 사용할 프롬프트 템플릿입니다. 사용자 쿼리를 구조화된 JSON으로 변환하는 역할을 합니다.

3.  **`backend/src/app/prompts/policy_grading_prompt.jinja2`**:
    *   `grade_policies` 노드(LLM Grader)에서 사용할 프롬프트 템플릿입니다. DB와 웹 검색 결과를 종합하여 재정렬하는 역할을 합니다.

4.  **`RAG_WORKFLOW_IMPROVEMENT.md`**:
    *   현재 보고서 파일입니다.

### 3.2. 수정된 파일

1.  **`backend/src/app/services/policy_search_service.py`**:
    *   기존의 `hybrid_search` 내 복잡한 분기 로직을 제거했습니다.
    *   새로 생성된 `search_workflow`를 호출하여 검색을 수행하도록 로직을 단순화하고, LangSmith 추적을 위한 설정을 추가했습니다.

2.  **`backend/src/app/agent/state.py`**:
    *   `SearchState`에 웹 검색 결과를 저장하기 위한 `web_search_results` 필드를 추가했습니다.

3.  **`backend/src/app/db/models.py`**:
    *   `Policy` ORM 모델에 `to_dict()` 메서드를 추가하여 LLM 프롬프트에서 객체를 쉽게 직렬화할 수 있도록 개선했습니다. (해당 파일은 컨텍스트에 없어 diff를 생성하지 않았습니다.)

### 3.3. 새로운 검색 워크플로우

```
START
  |
  v
[ query_understanding_node ]  // LLM으로 쿼리 분석 (키워드, 필터, 정렬 추출)
  |
  v
[ retrieve_policies_node ]    // Qdrant + MySQL에서 정책 검색, Top-1 유사도 계산
  |
  v
< check_sufficiency > --------- (유사도 >= 0.65) --------> [ END ]
  |
  | (유사도 < 0.65)
  v
[ web_search_node ]           // Tavily로 웹 검색 수행
  |
  v
[ grade_policies_node ]       // LLM Grader가 DB + 웹 결과 재정렬
  |
  v
[ END ]
```

- **핵심 파라미터**:
    - **충분성 판단 임계값 (Sufficiency Threshold)**: `0.65`

이러한 구조적 변경을 통해 검색 시스템은 더욱 지능적이고, 확장 가능하며, 유지보수가 용이한 아키텍처를 갖추게 되었습니다.