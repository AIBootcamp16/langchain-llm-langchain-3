# Search Agent v2.0 고도화 결과 보고서

## 개요

정책 검색 API를 **LangGraph 기반 에이전트 워크플로우 v2.0**으로 고도화했습니다.
**주요 개선:** 3단계 충분성 검증, 성능 최적화, LangSmith 연동 강화

---

## 1. 버전 비교

### v1.0 (이전)
```
워크플로우:
START → query_understanding → retrieve → check_sufficiency
                                                ↓
          summarize (LLM) ← [충분] | [부족] → web_search → summarize → END

문제점:
- 충분성 검사가 단순 (top_1 점수만 확인)
- summarize 노드에서 LLM 호출로 지연 발생
- 중간 신뢰도 구간에서 잘못된 판단 가능
```

### v2.0 (현재)
```
워크플로우:
START → query_understanding → retrieve → check_sufficiency (3단계)
                                                ↓
            finalize ← [충분] | [부족] → web_search → finalize → END

개선점:
✅ 3단계 충분성 검증 (Top-K → Cosine → LLM Grader)
✅ summarize 노드 제거 → finalize 노드로 대체 (LLM 호출 감소)
✅ 성능 최적화 (응답 속도 개선)
✅ LangSmith 연동 강화
```

---

## 2. 3단계 충분성 검증 시스템

### 2.1 검증 단계

```
┌─────────────────────────────────────────────────────────────────────┐
│                   3-Stage Sufficiency Check                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐                                                  │
│  │   1단계       │   top_1 유사도 >= 0.65?                          │
│  │  Top-K 검사   │                                                  │
│  └───────┬───────┘                                                  │
│          │                                                          │
│          ├── 실패 (< 0.65) ──────────────────▶ 웹 검색             │
│          │                                                          │
│          ▼ 통과                                                     │
│  ┌───────────────┐                                                  │
│  │   2단계       │   평균 유사도 >= 0.60?                           │
│  │ Cosine 재검증 │   또는 고점수(0.70+) 결과 >= 1개?               │
│  └───────┬───────┘                                                  │
│          │                                                          │
│          ├── 실패 ────────────────────────────▶ 웹 검색             │
│          │                                                          │
│          ▼ 통과                                                     │
│  ┌───────────────┐                                                  │
│  │   분기 판단   │   top_score >= 0.75?                            │
│  └───────┬───────┘                                                  │
│          │                                                          │
│          ├── Yes (고신뢰도) ──────────────────▶ 충분 (스킵 3단계)  │
│          │                                                          │
│          ▼ No (중간 신뢰도: 0.65~0.75)                              │
│  ┌───────────────┐                                                  │
│  │   3단계       │   LLM이 쿼리-결과 관련성 평가                    │
│  │  LLM Grader   │   relevance_score >= 0.70?                      │
│  └───────┬───────┘                                                  │
│          │                                                          │
│          ├── 통과 ────────────────────────────▶ 충분               │
│          └── 실패 ────────────────────────────▶ 웹 검색             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 기준값 상수

| 상수 | 값 | 설명 |
|------|-----|------|
| `SCORE_THRESHOLD_TOP1` | 0.65 | 1단계: top_1 유사도 기준 |
| `SCORE_THRESHOLD_COSINE` | 0.60 | 2단계: 평균 유사도 기준 |
| `HIGH_SCORE_THRESHOLD` | 0.70 | 고점수 결과 기준 |
| `LLM_GRADER_THRESHOLD` | 0.70 | 3단계: LLM 관련성 점수 기준 |
| `MIN_RESULTS_COUNT` | 2 | 최소 결과 수 |

### 2.3 LLM Grader 상세

**사용 조건:** 0.65 <= top_score < 0.75 (중간 신뢰도 구간)

**평가 기준:**
1. 키워드 매칭: 쿼리의 핵심 키워드가 정책에 포함되어 있는가?
2. 의미적 관련성: 쿼리의 의도와 정책의 목적이 일치하는가?
3. 대상 그룹 일치: 쿼리에서 언급된 대상과 정책 대상이 맞는가?
4. 지역 일치: 쿼리에서 언급된 지역과 정책 지역이 맞는가?

**프롬프트 파일:** `prompts/search_grader.jinja2`

---

## 3. 변경된 파일 목록

### 3.1 수정된 파일 (5개)

| 파일 경로 | 변경 내용 | 변경량 |
|-----------|----------|--------|
| `agent/nodes/search/search_check_node.py` | 3단계 충분성 검증 로직 적용 | 전체 재작성 (~300 LOC) |
| `agent/nodes/search/search_retrieve_node.py` | 성능 최적화 (threshold, limit 조정) | +20 LOC |
| `agent/workflows/search_workflow.py` | finalize 노드 추가, summarize 제거 | 전체 재작성 (~360 LOC) |
| `main.py` | LangSmith 초기화 로직 개선, API prefix 수정 | +20 LOC |
| `observability/langsmith_client.py` | 환경변수 설정 추가 | 기존 유지 |

### 3.2 신규 파일 (1개)

| 파일 경로 | 설명 | LOC |
|-----------|------|-----|
| `prompts/search_grader.jinja2` | LLM Grader 프롬프트 | 45 |

### 3.3 삭제/비활성화된 기능

| 항목 | 설명 |
|------|------|
| `summarize_results_node` | finalize_results_node로 대체 (LLM 호출 제거) |
| LLM 요약 생성 | 간단한 템플릿 기반 요약으로 대체 |

---

## 4. 성능 최적화 상세

### 4.1 검색 성능 개선

| 항목 | 이전 | 현재 | 개선 효과 |
|------|------|------|----------|
| Qdrant limit | 20 | 30 | 더 많은 후보 확보 |
| score_threshold | 0.50 | 0.45 | 낮은 유사도 결과도 후보에 포함 |
| summarize LLM 호출 | 항상 실행 | 제거 | 1회 LLM 호출 감소 |
| LLM Grader | 없음 | 0.65~0.75 구간만 | 필요시에만 LLM 호출 |

### 4.2 예상 응답 시간

| 케이스 | 예상 시간 |
|--------|----------|
| 고신뢰도 결과 (top_1 >= 0.75) | ~1.5s (LLM 1회: query_understanding) |
| 중간 신뢰도 결과 (0.65~0.75) | ~2.5s (LLM 2회: query_understanding + grader) |
| 웹 검색 필요 | ~3.5s (LLM 1~2회 + Tavily) |
| v1.0 평균 | ~3s (LLM 2회: query_understanding + summarize) |

---

## 5. LangSmith 연동

### 5.1 설정 방법

**1. 환경 변수 설정 (.env)**
```env
LANGSMITH_API_KEY=lsv2_pt_your-api-key-here
LANGSMITH_PROJECT=policy-search-agent
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

**2. 서버 시작 시 로그 확인**
```
INFO: LangSmith tracing enabled
      project: policy-search-agent
      endpoint: https://api.smith.langchain.com
      client_initialized: True
```

### 5.2 트레이싱 포인트 (v2.0)

| 노드 | 트레이스 이름 | run_type | 태그 |
|------|-------------|----------|------|
| Query Understanding | `query_understanding` | llm | node, search, llm, query-analysis |
| Retrieve | `search_retrieve` | retriever | node, search, retrieval, qdrant, mysql |
| Check Sufficiency | `search_check_sufficiency` | chain | node, search, check, 3-stage |
| LLM Grader | `llm_grader` | llm | node, search, llm, grader |
| Web Search | `search_web_search` | tool | node, search, web-search, tavily |
| Finalize | `finalize_results` | chain | node, search, finalize |

### 5.3 LangSmith 대시보드에서 확인 가능한 정보

1. **워크플로우 전체 흐름** - 각 노드 실행 순서 및 분기
2. **3단계 충분성 검증 과정** - 각 단계별 통과/실패 사유
3. **LLM Grader 결과** - 관련성 점수 및 판단 사유
4. **실행 시간** - 각 노드별 소요 시간
5. **토큰 사용량** - LLM 호출별 input/output 토큰

---

## 6. API 사용법

### 6.1 엔드포인트

```
GET /api/policies/search?query={검색어}&session_id={세션ID}
```

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| query | O | 검색 쿼리 |
| session_id | X | 세션 ID (미입력 시 자동 생성) |

### 6.2 응답 형식

```json
{
    "session_id": "abc-123",
    "summary": "'프리랜서 지원금' 검색 결과 5건을 찾았습니다. '프리랜서 창업 지원 사업'이(가) 가장 관련도가 높습니다(유사도: 85%).",
    "policies": [
        {
            "id": 1,
            "program_name": "프리랜서 창업 지원 사업",
            "region": "서울",
            "category": "사업화",
            "score": 0.85,
            "source_type": "internal"
        }
    ],
    "total_count": 5,
    "parsed_query": {
        "intent": "condition_search",
        "keywords": ["프리랜서", "지원금"],
        "filters": {"target_group": "프리랜서"},
        "sort_preference": "relevance"
    },
    "top_score": 0.85,
    "is_sufficient": true,
    "sufficiency_reason": "[충분] 고신뢰도 검색 결과.\n[1단계 Top-K] top_1=0.85 (기준: 0.65) → 통과\n[2단계 Cosine] 평균 유사도: 0.72, 고점수(0.70+) 결과: 3건 → 통과\n[고신뢰도] top_score=0.85 >= 0.75, 고점수 결과 있음 → LLM Grader 스킵",
    "web_sources": []
}
```

### 6.3 테스트 명령어

```bash
# 기본 검색
curl "http://localhost:8000/api/policies/search?query=창업%20지원금"

# 최신 정책 검색 (자동 정렬)
curl "http://localhost:8000/api/policies/search?query=최신%20청년%20정책"

# 지역 + 대상 그룹 검색
curl "http://localhost:8000/api/policies/search?query=서울%20프리랜서%20지원"

# 웹 검색 트리거 테스트 (DB에 없는 정책)
curl "http://localhost:8000/api/policies/search?query=2024년%20새로운%20AI%20로봇%20특허%20지원"
```

---

## 7. 실행 및 확인 방법

### 7.1 LangSmith 실행 + 확인 방법

**1. LangSmith 계정 생성 및 API 키 발급**
- https://smith.langchain.com 접속
- 로그인 후 Settings → API Keys에서 키 생성

**2. 환경 변수 설정**
```bash
# .env 파일에 추가
LANGSMITH_API_KEY=lsv2_pt_xxxxx
LANGSMITH_PROJECT=policy-search-agent
LANGSMITH_TRACING=true
```

**3. 서버 재시작 후 API 호출**
```bash
curl "http://localhost:8000/api/policies/search?query=프리랜서"
```

**4. LangSmith 대시보드 확인**
- https://smith.langchain.com/o/{org-id}/projects/{project-id}/runs
- 해당 프로젝트의 Runs 탭에서 워크플로우 확인
- 각 노드 클릭하여 상세 정보 확인

### 7.2 Backend API 실행 + 확인 방법

**1. Docker Compose로 실행**
```bash
cd /mnt/c/Users/julia/fastcampus/LangChain_project
docker-compose up -d
```

**2. 서버 상태 확인**
```bash
# 헬스체크
curl http://localhost:8000/health

# API 문서 확인
open http://localhost:8000/docs
```

**3. 검색 API 테스트**
```bash
# Search Agent API (고도화된 검색)
curl "http://localhost:8000/api/policies/search?query=프리랜서%20지원금"

# Legacy API (기존 검색)
curl "http://localhost:8000/api/policies?query=프리랜서"
```

**4. 로그 확인**
```bash
docker logs -f langchain_project-backend-1
```

### 7.3 Frontend 실행 + 확인 방법

**1. Frontend 서버 실행**
```bash
cd /mnt/c/Users/julia/fastcampus/LangChain_project/frontend
npm install
npm run dev
```

**2. 브라우저에서 확인**
```
http://localhost:3000
```

**3. 검색 테스트**
- 홈 화면에서 검색어 입력 (예: "프리랜서 지원금")
- 검색 버튼 클릭 또는 Enter
- 결과 페이지에서 정책 리스트 확인

**4. 문제 발생 시 확인**
- 브라우저 개발자 도구 (F12) → Network 탭
- `/api/policies/search` 요청 확인
- Response 내용 확인

---

## 8. 정량적 개선 지표

| 지표 | v1.0 | v2.0 | 개선 |
|------|------|------|------|
| 충분성 검사 단계 | 1단계 | 3단계 | 정확도 향상 |
| 평균 LLM 호출 수 | 2회 | 1~2회 | 최대 50% 감소 |
| summarize LLM 호출 | 항상 | 없음 | 제거됨 |
| LLM Grader 호출 | 없음 | 필요시만 | 효율적 사용 |
| 중간 신뢰도 오탐 | 가능 | LLM 검증 | 감소 |
| score_threshold | 0.50 | 0.45 | 후보 증가 |
| Qdrant limit | 20 | 30 | 후보 증가 |
| 트레이싱 범위 | 기본 | 3단계 상세 | 디버깅 용이 |

---

## 9. 정성적 개선 사항

### 9.1 검색 품질 개선

1. **3단계 충분성 검증**: 단순 점수 기반에서 다단계 검증으로 개선
2. **LLM Grader**: 중간 신뢰도 구간에서 LLM이 관련성을 재평가
3. **낮은 threshold**: 더 많은 후보를 확보하여 누락 감소

### 9.2 성능 개선

1. **summarize 제거**: 불필요한 LLM 호출 제거
2. **고신뢰도 스킵**: top_score >= 0.75면 LLM Grader 스킵
3. **finalize 노드**: 단순 데이터 변환만 수행 (LLM 없음)

### 9.3 운영/디버깅 개선

1. **LangSmith 연동 강화**: 3단계 검증 과정 상세 트레이싱
2. **sufficiency_reason 상세화**: 각 단계별 통과/실패 사유 기록
3. **환경 변수 검증**: API 키 없으면 명확한 로그 출력

---

## 10. 파일 구조 (최종)

```
backend/src/app/
├── agent/
│   ├── state.py                              # SearchState
│   ├── controller.py                         # run_search()
│   ├── nodes/
│   │   ├── search/
│   │   │   ├── __init__.py
│   │   │   ├── query_understanding_node.py   # LLM 쿼리 분석
│   │   │   ├── search_retrieve_node.py       # Qdrant+MySQL 검색 [수정]
│   │   │   ├── search_check_node.py          # 3단계 충분성 검사 [전체 재작성]
│   │   │   ├── search_web_node.py            # Tavily 웹 검색
│   │   │   └── summarize_node.py             # (비활성화됨)
│   │   └── ...
│   └── workflows/
│       ├── __init__.py
│       ├── qa_workflow.py
│       └── search_workflow.py                # v2.0 워크플로우 [전체 재작성]
├── api/
│   └── routes_policy.py                      # /policies/search
├── prompts/
│   ├── search_query_understanding.jinja2
│   ├── search_summarize_results.jinja2       # (비활성화됨)
│   └── search_grader.jinja2                  # [신규] LLM Grader 프롬프트
├── observability/
│   ├── __init__.py
│   ├── langsmith_client.py                   # LangSmith 클라이언트
│   └── tracing.py                            # 트레이싱 데코레이터
└── main.py                                   # LangSmith 초기화 [수정]
```

---

## 11. 트러블슈팅

### 11.1 Frontend 검색 결과가 안 나옴

**원인:** API prefix 불일치 (`/api/v1` vs `/api`)

**해결:** `main.py`에서 `/api` prefix 라우터 추가됨
```python
# API routes (frontend 호환성 - /api prefix)
app.include_router(routes_policy.router, prefix="/api", tags=["Policies"])
```

### 11.2 LangSmith 프로젝트가 안 보임

**원인:** 환경 변수 미설정 또는 API 키 오류

**확인 방법:**
1. `.env` 파일 확인
2. 서버 로그에서 "LangSmith tracing enabled" 확인
3. `client_initialized: True` 확인

**해결:**
```env
LANGSMITH_API_KEY=lsv2_pt_xxxx  # 유효한 키인지 확인
LANGSMITH_TRACING=true          # true로 설정
```

### 11.3 검색 속도가 느림

**원인:** LLM 호출 횟수

**확인:**
- LangSmith에서 어느 노드가 오래 걸리는지 확인
- query_understanding이 대부분의 시간 차지

**최적화 방안:**
- OpenAI 모델을 `gpt-3.5-turbo`로 변경 (속도 향상, 품질 하락)
- query_understanding 캐싱 적용 (동일 쿼리)

---

## 작성 정보

- **작성일:** 2026-01-14
- **버전:** v2.0.0
- **LangGraph 버전:** 0.0.20+
- **주요 변경:** 3단계 충분성 검증, 성능 최적화, LangSmith 연동 강화
