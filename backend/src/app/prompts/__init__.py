"""
Prompt Templates
Jinja2 템플릿 렌더링 유틸리티
"""

import os
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

# 템플릿 디렉토리 경로
TEMPLATE_DIR = Path(__file__).parent

# Jinja2 환경 설정
env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Jinja2 템플릿 렌더링
    
    Args:
        template_name: 템플릿 파일명 (예: 'policy_qa_docs_only_prompt.jinja2')
        context: 템플릿 변수 딕셔너리
    
    Returns:
        str: 렌더링된 프롬프트
    """
    template = env.get_template(template_name)
    return template.render(**context)


__all__ = ['render_template']

