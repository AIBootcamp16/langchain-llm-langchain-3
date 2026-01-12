"""
LangSmith 트레이싱 데코레이터 및 유틸리티
워크플로우 및 LLM 호출을 트레이싱합니다.
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from langsmith import traceable

from .langsmith_client import get_langsmith_client
from ..config.logger import get_logger

logger = get_logger()

F = TypeVar('F', bound=Callable[..., Any])


def trace_workflow(
    name: str,
    tags: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    run_type: str = "chain"
) -> Callable[[F], F]:
    """
    워크플로우 실행을 트레이싱하는 데코레이터
    
    Args:
        name: 트레이스 이름
        tags: 태그 리스트
        metadata: 메타데이터
        run_type: 실행 타입 (chain, tool, llm, etc.)
    
    Returns:
        Callable: 데코레이터 함수
    
    Example:
        ```python
        @trace_workflow(
            name="qa_workflow",
            tags=["qa", "policy-123"],
            metadata={"workflow_type": "qa"}
        )
        def run_qa_workflow(state):
            # ... workflow logic
            return state
        ```
    """
    def decorator(func: F) -> F:
        client = get_langsmith_client()
        
        if not client.is_enabled():
            # LangSmith가 비활성화된 경우 원본 함수 반환
            return func
        
        @wraps(func)
        @traceable(
            name=name,
            tags=tags or [],
            metadata=metadata or {},
            run_type=run_type
        )
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                logger.debug(
                    f"Starting traced workflow: {name}",
                    extra={
                        "workflow": name,
                        "tags": tags,
                        "run_type": run_type
                    }
                )
                result = func(*args, **kwargs)
                logger.debug(
                    f"Completed traced workflow: {name}",
                    extra={"workflow": name}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Error in traced workflow: {name}",
                    extra={
                        "workflow": name,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        return cast(F, wrapper)
    return decorator


def trace_llm_call(
    name: str,
    tags: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    LLM 호출을 트레이싱하는 데코레이터
    
    Args:
        name: 트레이스 이름
        tags: 태그 리스트
        metadata: 메타데이터
    
    Returns:
        Callable: 데코레이터 함수
    
    Example:
        ```python
        @trace_llm_call(
            name="generate_answer",
            tags=["llm", "answer-generation"],
            metadata={"model": "gpt-4"}
        )
        def generate_answer(prompt: str) -> str:
            # ... LLM call
            return answer
        ```
    """
    return trace_workflow(
        name=name,
        tags=tags,
        metadata=metadata,
        run_type="llm"
    )


def trace_retrieval(
    name: str,
    tags: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    검색(Retrieval) 작업을 트레이싱하는 데코레이터
    
    Args:
        name: 트레이스 이름
        tags: 태그 리스트
        metadata: 메타데이터
    
    Returns:
        Callable: 데코레이터 함수
    """
    return trace_workflow(
        name=name,
        tags=tags,
        metadata=metadata,
        run_type="retriever"
    )


def trace_tool(
    name: str,
    tags: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    도구(Tool) 실행을 트레이싱하는 데코레이터
    
    Args:
        name: 트레이스 이름
        tags: 태그 리스트
        metadata: 메타데이터
    
    Returns:
        Callable: 데코레이터 함수
    """
    return trace_workflow(
        name=name,
        tags=tags,
        metadata=metadata,
        run_type="tool"
    )

