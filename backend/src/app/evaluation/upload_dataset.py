"""
LangSmith에 평가 데이터셋 업로드
"""

from langsmith import Client
from .datasets import QA_EVALUATION_DATASET
from ..config.logger import get_logger

logger = get_logger()


def upload_evaluation_dataset():
    """LangSmith에 평가 데이터셋 업로드"""
    client = Client()
    
    # 데이터셋 이름
    dataset_name = "qaagent-policy-qa-eval-v1"
    
    try:
        # 기존 데이터셋이 있으면 삭제 (optional)
        try:
            client.delete_dataset(dataset_name=dataset_name)
            logger.info(f"기존 데이터셋 '{dataset_name}' 삭제됨")
        except:
            pass
        
        # 새 데이터셋 생성
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="QA Agent 평가 데이터셋 (v1) - 정책 QA, 웹 검색, 하이브리드",
        )
        logger.info(f"데이터셋 '{dataset_name}' 생성됨 (ID: {dataset.id})")
        
        # 데이터 추가
        for i, example in enumerate(QA_EVALUATION_DATASET):
            client.create_example(
                inputs=example["input"],
                outputs=example["expected_output"],
                dataset_id=dataset.id,
                metadata=example["metadata"]
            )
            logger.info(f"예시 {i+1}/{len(QA_EVALUATION_DATASET)} 추가됨")
        
        logger.info(f"\n✅ 데이터셋 '{dataset_name}' 업로드 완료!")
        logger.info(f"   - 총 {len(QA_EVALUATION_DATASET)}개 예시")
        logger.info(f"   - 데이터셋 ID: {dataset.id}")
        
        return dataset
        
    except Exception as e:
        logger.error(f"데이터셋 업로드 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    upload_evaluation_dataset()

