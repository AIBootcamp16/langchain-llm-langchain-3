"""
QA Agent 평가 데이터셋
"""

QA_EVALUATION_DATASET = [
    # 1. 정책 내용 질문 (문서 충분)
    {
        "input": {
            "session_id": "eval_001",
            "policy_id": 507,  # 예비창업패키지
            "current_query": "지원 금액은 얼마인가요?",
        },
        "expected_output": {
            "answer_should_contain": ["8억", "억원"],
            "evidence_type": "internal",
            "citation_format": "[정책문서 X]",
        },
        "metadata": {
            "category": "policy_qa_sufficient",
            "difficulty": "easy"
        }
    },
    
    # 2. 링크 요청 (웹 검색)
    {
        "input": {
            "session_id": "eval_002",
            "policy_id": 507,
            "current_query": "신청 링크 알려줘",
        },
        "expected_output": {
            "query_type": "WEB_ONLY",
            "evidence_type": "web",
            "citation_format": "[웹 X]",
        },
        "metadata": {
            "category": "web_only",
            "difficulty": "easy"
        }
    },
    
    # 3. 복잡한 질문 (하이브리드)
    {
        "input": {
            "session_id": "eval_003",
            "policy_id": 507,
            "current_query": "최근 변경사항이 있나요?",
        },
        "expected_output": {
            "need_web_search": True,
            "evidence_types": ["internal", "web"],
            "answer_should_contain": ["정책문서", "웹"],
        },
        "metadata": {
            "category": "policy_qa_hybrid",
            "difficulty": "hard"
        }
    },
    
    # 4. 신청 자격 질문
    {
        "input": {
            "session_id": "eval_004",
            "policy_id": 507,
            "current_query": "신청 자격이 어떻게 되나요?",
        },
        "expected_output": {
            "answer_should_contain": ["예비창업자", "39세"],
            "evidence_type": "internal",
        },
        "metadata": {
            "category": "policy_qa_sufficient",
            "difficulty": "easy"
        }
    },
    
    # 5. 애매한 질문 (분류 어려움)
    {
        "input": {
            "session_id": "eval_005",
            "policy_id": 507,
            "current_query": "이 정책 어디서 신청해요?",
        },
        "expected_output": {
            "query_type": "WEB_ONLY",  # "어디서 신청" → 링크 요청으로 분류되어야 함
        },
        "metadata": {
            "category": "classification_test",
            "difficulty": "medium"
        }
    },
    
    # 6. 지원 대상 질문
    {
        "input": {
            "session_id": "eval_006",
            "policy_id": 507,
            "current_query": "누가 신청할 수 있나요?",
        },
        "expected_output": {
            "answer_should_contain": ["예비창업자", "만 39세 이하"],
            "evidence_type": "internal",
            "citation_format": "[정책문서 X]",
        },
        "metadata": {
            "category": "policy_qa_sufficient",
            "difficulty": "easy"
        }
    },
    
    # 7. 지원 기간 질문
    {
        "input": {
            "session_id": "eval_007",
            "policy_id": 507,
            "current_query": "언제까지 신청할 수 있어요?",
        },
        "expected_output": {
            "answer_should_contain": ["접수", "기간", "신청"],
            "evidence_type": "internal",
        },
        "metadata": {
            "category": "policy_qa_sufficient",
            "difficulty": "easy"
        }
    },
    
    # 8. 홈페이지 요청
    {
        "input": {
            "session_id": "eval_008",
            "policy_id": 507,
            "current_query": "홈페이지 주소 알려줘",
        },
        "expected_output": {
            "query_type": "WEB_ONLY",
            "evidence_type": "web",
        },
        "metadata": {
            "category": "web_only",
            "difficulty": "easy"
        }
    },
]

