"""
Search Configuration
검색 설정 및 동적 유사도 조정 기능

이 파일에서 검색 관련 설정을 쉽게 변경할 수 있습니다.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class SimilarityStrategy(Enum):
    """유사도 조정 전략"""
    FIXED = "fixed"           # 고정 임계값 사용
    ADAPTIVE = "adaptive"     # 결과 수에 따라 동적 조정
    PROGRESSIVE = "progressive"  # 점진적으로 임계값 낮춤


class SearchMode(Enum):
    """검색 모드"""
    DENSE = "dense"           # Dense (벡터) 검색만
    SPARSE = "sparse"         # Sparse (BM25) 검색만
    HYBRID = "hybrid"         # Dense + Sparse 하이브리드


@dataclass
class SearchConfig:
    """
    검색 설정 클래스

    이 클래스를 수정하여 검색 동작을 조정할 수 있습니다.
    """

    # ==========================================================================
    # 기본 유사도 임계값 설정
    # ==========================================================================

    # 기본 유사도 임계값 (0.0 ~ 1.0)
    # 낮을수록 더 많은 결과, 높을수록 더 정확한 결과
    default_score_threshold: float = 0.25

    # 최소 유사도 임계값 (이 값보다 낮으면 결과에서 제외)
    min_score_threshold: float = 0.15

    # 최대 유사도 임계값 (적응형 조정 시 이 값을 초과하지 않음)
    max_score_threshold: float = 0.50

    # ==========================================================================
    # 적응형 유사도 조정 설정
    # ==========================================================================

    # 유사도 조정 전략
    similarity_strategy: SimilarityStrategy = SimilarityStrategy.ADAPTIVE

    # 목표 최소 결과 수 (이보다 적으면 유사도를 낮춤)
    target_min_results: int = 3

    # 목표 최대 결과 수 (이보다 많으면 유사도를 높임)
    target_max_results: int = 15

    # 적응형 조정 시 임계값 변경 단위
    threshold_step: float = 0.05

    # ==========================================================================
    # 검색 수량 설정
    # ==========================================================================

    # Qdrant에서 가져올 최대 후보 수 (내부 처리용)
    qdrant_limit: int = 100

    # 최종 반환 결과 수
    result_limit: int = 50

    # ==========================================================================
    # 웹 검색 충분성 설정
    # ==========================================================================

    # 웹 검색 트리거 조건: 결과 수가 이보다 적으면 웹 검색 수행
    web_search_trigger_count: int = 2

    # 웹 검색 트리거 조건: 최고 점수가 이보다 낮으면 웹 검색 수행
    web_search_trigger_score: float = 0.35

    # 웹 검색 최대 결과 수
    web_search_max_results: int = 5

    # ==========================================================================
    # 하이브리드 검색 설정 (Dense + Sparse)
    # ==========================================================================

    # 검색 모드 (dense, sparse, hybrid)
    search_mode: SearchMode = SearchMode.HYBRID

    # Dense 검색 가중치 (0.0 ~ 1.0, hybrid 모드에서 사용)
    dense_weight: float = 0.7

    # Sparse 검색 가중치 (0.0 ~ 1.0, hybrid 모드에서 사용)
    sparse_weight: float = 0.3

    # RRF (Reciprocal Rank Fusion) 사용 여부
    # True: 순위 기반 결합, False: 점수 가중 평균
    use_rrf: bool = True

    # RRF k 파라미터 (높을수록 순위 차이 영향 감소)
    rrf_k: int = 60

    # Sparse 검색 최소 점수 (BM25)
    sparse_min_score: float = 0.1

    # ==========================================================================
    # 키워드별 유사도 가중치 (특정 키워드에 대해 다른 임계값 적용)
    # ==========================================================================

    # 키워드별 유사도 조정 (예: 특정 키워드는 더 낮은/높은 임계값)
    keyword_threshold_adjustments: Dict[str, float] = field(default_factory=lambda: {
        # 일반적인 키워드는 낮은 임계값 (더 많은 결과)
        "지원금": -0.05,
        "보조금": -0.05,
        "지원사업": -0.05,
        "정책": -0.05,
        "창업": -0.05,
        "청년": -0.05,
        "중소기업": -0.05,
        "소상공인": -0.05,
        # 구체적인 키워드는 높은 임계값 (더 정확한 결과)
        "R&D": 0.05,
        "수출": 0.05,
        "특허": 0.05,
    })

    # ==========================================================================
    # 지역/카테고리별 유사도 조정
    # ==========================================================================

    # 지역별 유사도 조정
    region_threshold_adjustments: Dict[str, float] = field(default_factory=lambda: {
        "전국": -0.05,  # 전국 검색은 더 넓게
    })

    # 카테고리별 유사도 조정
    category_threshold_adjustments: Dict[str, float] = field(default_factory=lambda: {})

    def calculate_threshold(
        self,
        keywords: List[str] = None,
        region: str = None,
        category: str = None,
        current_result_count: int = None
    ) -> float:
        """
        동적으로 유사도 임계값 계산

        Args:
            keywords: 검색 키워드 리스트
            region: 지역 필터
            category: 카테고리 필터
            current_result_count: 현재 결과 수 (적응형 조정용)

        Returns:
            float: 계산된 유사도 임계값
        """
        threshold = self.default_score_threshold

        # 키워드별 조정
        if keywords:
            for keyword in keywords:
                for kw, adjustment in self.keyword_threshold_adjustments.items():
                    if kw in keyword:
                        threshold += adjustment
                        break

        # 지역별 조정
        if region and region in self.region_threshold_adjustments:
            threshold += self.region_threshold_adjustments[region]

        # 카테고리별 조정
        if category and category in self.category_threshold_adjustments:
            threshold += self.category_threshold_adjustments[category]

        # 적응형 조정: 결과 수에 따라
        if self.similarity_strategy == SimilarityStrategy.ADAPTIVE and current_result_count is not None:
            if current_result_count < self.target_min_results:
                # 결과가 적으면 임계값 낮춤
                threshold -= self.threshold_step
            elif current_result_count > self.target_max_results:
                # 결과가 많으면 임계값 높임
                threshold += self.threshold_step

        # 범위 제한
        threshold = max(self.min_score_threshold, min(self.max_score_threshold, threshold))

        return threshold

    def should_trigger_web_search(
        self,
        result_count: int,
        top_score: float
    ) -> bool:
        """
        웹 검색을 트리거해야 하는지 판단

        Args:
            result_count: 현재 검색 결과 수
            top_score: 최고 유사도 점수

        Returns:
            bool: 웹 검색 필요 여부
        """
        # 결과가 적거나 점수가 낮으면 웹 검색
        return (
            result_count < self.web_search_trigger_count or
            top_score < self.web_search_trigger_score
        )


# 전역 설정 인스턴스 (싱글톤)
_search_config: Optional[SearchConfig] = None


def get_search_config() -> SearchConfig:
    """
    검색 설정 인스턴스 반환 (싱글톤)

    Returns:
        SearchConfig: 검색 설정 인스턴스
    """
    global _search_config
    if _search_config is None:
        _search_config = SearchConfig()
    return _search_config


def update_search_config(**kwargs) -> SearchConfig:
    """
    검색 설정 업데이트

    Args:
        **kwargs: 업데이트할 설정 값들

    Returns:
        SearchConfig: 업데이트된 검색 설정

    Example:
        update_search_config(default_score_threshold=0.30, target_min_results=5)
    """
    global _search_config
    config = get_search_config()

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config
