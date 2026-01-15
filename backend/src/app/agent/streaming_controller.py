"""
Streaming QA Controller
스트리밍 방식 Q&A 처리 컨트롤러
"""

import json
from typing import Dict, Any, AsyncGenerator

from ..config.logger import get_logger
from ..cache import get_chat_cache, get_policy_cache
from ..llm.openai_client import get_openai_client
from ..prompts import render_template
from .nodes import classify_query_type_node, load_cached_docs_node, check_sufficiency_node
from ..web_search.clients.tavily_client import TavilyClient

logger = get_logger()
chat_cache = get_chat_cache()
policy_cache = get_policy_cache()
llm_client = get_openai_client()


class StreamingQAController:
    """
    스트리밍 Q&A 컨트롤러
    
    워크플로우를 간소화하여 스트리밍 응답 생성
    """
    
    def __init__(self):
        """Initialize streaming controller"""
        self.tavily_client = TavilyClient()
    
    async def process_query_stream(
        self,
        session_id: str,
        policy_id: int,
        user_query: str
    ) -> AsyncGenerator[str, None]:
        """
        사용자 질문을 스트리밍 방식으로 처리
        
        Args:
            session_id: 세션 ID
            policy_id: 정책 ID
            user_query: 사용자 질문
        
        Yields:
            str: SSE 형식의 JSON 데이터
        """
        try:
            # 1. 초기 상태 생성
            state = {
                "session_id": session_id,
                "policy_id": policy_id,
                "current_query": user_query,
                "chat_history": chat_cache.get_chat_history(session_id),
                "retrieved_docs": [],
                "web_results": [],
                "query_type": "POLICY_QA",
                "need_web_search": False
            }
            
            # 2. 쿼리 분류
            yield self._format_sse("status", {"step": "classifying", "message": "질문 분류 중..."})
            state = classify_query_type_node(state)
            query_type = state.get("query_type", "POLICY_QA")
            
            # 3. 문서 로드 또는 웹 검색
            if query_type == "WEB_ONLY":
                yield self._format_sse("status", {"step": "searching", "message": "웹 검색 중..."})
                web_results = await self._search_web(user_query)
                state["web_results"] = web_results
                template_name = "policy_qa_web_only_prompt.jinja2"
            else:
                # 캐시에서 문서 로드
                yield self._format_sse("status", {"step": "loading", "message": "문서 로드 중..."})
                state = load_cached_docs_node(state)
                
                # 캐시 미스 시 에러 이벤트 전송
                if not state.get("retrieved_docs") or len(state.get("retrieved_docs", [])) == 0:
                    error_msg = "정책 문서가 로드되지 않았습니다. 페이지를 새로고침해주세요."
                    logger.error(
                        "Cache miss - policy not initialized",
                        extra={"session_id": session_id, "policy_id": policy_id}
                    )
                    yield self._format_sse("error", {"message": error_msg, "code": "CACHE_MISS"})
                    return
                
                state = check_sufficiency_node(state)
                
                need_web_search = state.get("need_web_search", False)
                
                # 컨텍스트 타입 확인 (웹 공고 vs 정책 문서)
                context_type = state.get("context_type", "policy")
                
                if need_web_search:
                    yield self._format_sse("status", {"step": "searching", "message": "추가 정보 검색 중..."})
                    web_results = await self._search_web(user_query)
                    state["web_results"] = web_results
                    template_name = "policy_qa_hybrid_prompt.jinja2"
                else:
                    # 웹 공고인 경우 웹 전용 프롬프트 사용
                    if context_type == "web":
                        template_name = "policy_qa_web_only_prompt.jinja2"
                    else:
                        template_name = "policy_qa_docs_only_prompt.jinja2"
            
            # 4. 프롬프트 생성
            yield self._format_sse("status", {"step": "generating", "message": "답변 생성 중..."})
            prompt = self._build_prompt(state, template_name)
            logger.info(
                "Prompt generated",
                extra={
                    "session_id": session_id,
                    "template_name": template_name,
                    "context_type": state.get("context_type", "policy"),
                    "retrieved_docs_count": len(state.get("retrieved_docs", [])),
                    "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt
                }
            )
            
            # 5. 스트리밍 답변 생성
            full_answer = ""
            async for chunk in llm_client.generate_with_system_stream(
                system_prompt=prompt,
                user_message=user_query,
                temperature=0.0
            ):
                full_answer += chunk
                yield self._format_sse("chunk", {"content": chunk})
            
            # 5.5. 답변 불충분 체크 및 웹 검색 추가
            insufficient_keywords = [
                "정보가 포함되어 있지 않습니다", 
                "확인이 어렵습니다", 
                "정보가 부족", 
                "문서로는", 
                "찾을 수 없습니다",
                "명시되어 있지 않습니다",  # 추가
                "명시되어 있지 않",  # 추가
                "명시되지 않",  # 추가
                "포함되어 있지 않",  # 추가
                "제공되지 않",  # 추가
                "나와 있지 않"  # 추가
            ]
            is_insufficient = any(keyword in full_answer for keyword in insufficient_keywords)
            
            if is_insufficient and template_name == "policy_qa_docs_only_prompt.jinja2":
                logger.info(
                    "Answer insufficient, performing web search",
                    extra={"session_id": session_id, "query": user_query}
                )
                
                # 웹 검색 수행
                yield self._format_sse("status", {"step": "searching", "message": "추가 정보 검색 중..."})
                web_results = await self._search_web(user_query)
                state["web_results"] = web_results
                
                # 하이브리드 프롬프트로 재생성
                hybrid_prompt = self._build_prompt(state, "policy_qa_hybrid_prompt.jinja2")
                
                # 기존 답변에 웹 검색 결과 추가
                yield self._format_sse("status", {"step": "enhancing", "message": "웹 검색 결과 추가 중..."})
                
                # 헤더 먼저 전송
                header_text = "\n\n**추가 정보 (웹 검색):**\n"
                yield self._format_sse("chunk", {"content": header_text})
                
                additional_answer = header_text
                async for chunk in llm_client.generate_with_system_stream(
                    system_prompt=hybrid_prompt,
                    user_message=user_query,
                    temperature=0.0
                ):
                    additional_answer += chunk
                    yield self._format_sse("chunk", {"content": chunk})
                
                full_answer += additional_answer
            
            # 6. Evidence 추출 및 전송
            evidence = self._extract_evidence(state, full_answer)
            logger.info(
                "Evidence extracted",
                extra={
                    "session_id": session_id,
                    "evidence_count": len(evidence),
                    "evidence": evidence
                }
            )
            yield self._format_sse("evidence", {"evidence": evidence})
            
            # 7. 대화 히스토리 저장
            chat_cache.add_message(session_id, "USER", user_query)
            chat_cache.add_message(session_id, "ASSISTANT", full_answer)
            
            # 8. 완료 신호
            yield self._format_sse("done", {"message": "완료"})
            
        except Exception as e:
            logger.error(
                "Error in streaming query processing",
                extra={"error": str(e), "session_id": session_id},
                exc_info=True
            )
            yield self._format_sse("error", {"message": str(e)})
    
    async def _search_web(self, query: str) -> list:
        """웹 검색 수행"""
        try:
            results = self.tavily_client.search(query, max_results=5)
            return results.get("results", [])
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    def _build_prompt(self, state: Dict[str, Any], template_name: str) -> str:
        """프롬프트 생성"""
        policy_context = policy_cache.get_policy_context(state["session_id"])
        policy_info = policy_context.get("policy_info", {}) if policy_context else {}
        context_type = state.get("context_type", "policy")  # "policy" or "web"
        
        context = {
            "policy_name": policy_info.get("name", "정책"),
            "policy_overview": policy_info.get("overview", ""),
            "apply_target": policy_info.get("apply_target", ""),
            "support_description": policy_info.get("support_description", ""),
            "retrieved_docs": state.get("retrieved_docs", []),
            "web_results": state.get("web_results", []),
            "chat_history": state.get("chat_history", []),
            "user_question": state.get("current_query", ""),
            "context_type": context_type  # 웹/정책 구분 추가
        }
        
        
        prompt = render_template(template_name, context)
        
        return prompt
    
    def _extract_evidence(self, state: Dict[str, Any], answer: str) -> list:
        """답변에서 evidence 추출"""
        evidence = []
        
        # 정책 문서 또는 웹 공고 evidence
        docs = state.get("retrieved_docs", [])
        for idx, doc in enumerate(docs[:5], 1):
            doc_type = doc.get("doc_type", "")
            
            # 웹 공고인 경우 type을 "web"으로 설정하고 URL 포함
            if doc_type == "web_content":
                # url 또는 source 필드에서 URL 가져오기
                url = doc.get("url", "") or doc.get("source", "")
                evidence.append({
                    "type": "web",
                    "index": idx,
                    "title": "웹 공고",
                    "url": url,
                    "content": doc.get("content", "")[:200],
                    "doc_type": doc_type
                })
            else:
                # 정책 문서인 경우
                evidence.append({
                    "type": "policy",
                    "index": idx,
                    "content": doc.get("content", "")[:200],
                    "doc_type": doc_type
                })
        
        # 웹 검색 evidence
        web_results = state.get("web_results", [])
        for idx, result in enumerate(web_results[:5], 1):
            evidence.append({
                "type": "web",
                "index": len(evidence) + 1,  # 이전 evidence 개수 + 1
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", "")[:200]
            })
        
        return evidence
    
    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        SSE (Server-Sent Events) 형식으로 데이터 포맷
        
        Args:
            event_type: 이벤트 타입 (status, chunk, evidence, done, error)
            data: 전송할 데이터
        
        Returns:
            str: SSE 형식 문자열
        """
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def get_streaming_controller() -> StreamingQAController:
    """Get streaming controller instance"""
    return StreamingQAController()

