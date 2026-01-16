# QA Agent + Search Feature 통합

## 📋 개요
QA Agent 브랜치에 새로운 검색 시스템(SimpleSearchService)을 통합하고, UI/UX 개선 작업을 수행.

## 🔧 주요 변경사항

### 1. 검색 시스템 개선
- **새로운 검색 서비스 통합**: `SimpleSearchService` (하이브리드 검색 - Dense + Sparse BM25)
- **기존 파일 삭제**: `policy_repo.py`, `qdrant_client.py`, `embedder_bge_m3.py` (검색 전용)
- **새로운 파일 추가**:
  - `backend/src/app/services/simple_search_service.py` - 하이브리드 검색
  - `backend/src/app/vector_store/sparse_search.py` - BM25 검색
  - `backend/src/app/services/search_config.py` - 검색 설정



### 2. 페이지네이션
- **구현 방식**: 모든 결과를 한 번에 가져와서 클라이언트에서 페이징
- **페이지 크기**: 7개
- **UI**: 이전/다음 버튼 + 페이지 번호 (현재 페이지 ±2 표시)


## 📂 파일 변경 요약

### 추가된 파일
- `backend/src/app/services/simple_search_service.py`
- `backend/src/app/vector_store/sparse_search.py`
- `backend/src/app/services/search_config.py`

### 삭제된 파일
- `backend/src/app/db/repositories/policy_repo.py` (검색 전용)
- ~~`backend/src/app/vector_store/qdrant_client.py`~~ ( QA Agent가 사용 중이므로 유지)
- ~~`backend/src/app/vector_store/embedder_bge_m3.py`~~ (QA Agent가 사용 중이므로 유지)

### 수정된 파일
- `backend/src/app/api/routes_policy.py` - 검색 API 경로 수정
- `backend/src/app/services/policy_search_service.py` - Legacy 엔드포인트 유지
- `backend/src/app/main.py` - Router prefix 수정
- `frontend/src/app/page.tsx` -수정정
- `frontend/src/app/search/page.tsx` - 새 API 사용 + 페이지네이션
- `frontend/src/lib/api.ts` - `searchPolicies()` 추가, `getPolicy()` 경로 수정
- `frontend/src/components/policy/PolicyCard.tsx` - 웹 결과 식별 로직 수정
- `frontend/src/store/usePolicyStore.ts` - 클라이언트 페이지네이션 지원



---

**최종 업데이트**: 2026-01-16
**브랜치**: `qa_search`

