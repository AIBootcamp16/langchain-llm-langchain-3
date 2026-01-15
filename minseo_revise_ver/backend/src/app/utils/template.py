import os
from jinja2 import Environment, FileSystemLoader, Template

def load_prompt(template_name: str) -> Template:
    """
    Jinja2 프롬프트 템플릿 로드
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # backend/src/app/utils -> backend/src/app/prompts
    prompts_dir = os.path.join(os.path.dirname(current_dir), "prompts")
    
    env = Environment(loader=FileSystemLoader(prompts_dir))
    return env.get_template(template_name)