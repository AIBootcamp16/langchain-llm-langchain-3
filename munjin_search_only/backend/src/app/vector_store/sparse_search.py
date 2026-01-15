"""
Sparse Search (BM25)
키워드 기반 희소 벡터 검색

Dense 검색과 결합하여 하이브리드 검색 지원
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

from ..config.logger import get_logger

logger = get_logger()


@dataclass
class BM25Config:
    """BM25 파라미터 설정"""
    k1: float = 1.5      # Term frequency saturation
    b: float = 0.75      # Length normalization
    epsilon: float = 0.25  # IDF smoothing


class KoreanTokenizer:
    """
    간단한 한국어 토크나이저

    형태소 분석기 없이 규칙 기반으로 토큰화
    """

    # 불용어 리스트
    STOPWORDS = {
        # 조사
        "은", "는", "이", "가", "을", "를", "의", "에", "에서", "로", "으로",
        "와", "과", "도", "만", "뿐", "부터", "까지", "에게", "한테", "께",
        # 접속사/부사
        "그리고", "그러나", "하지만", "또한", "또", "및", "등",
        # 일반적인 동사/형용사 어미
        "하다", "되다", "있다", "없다", "같다", "위한", "통한", "대한",
        # 기타
        "것", "수", "등", "중", "내", "외"
    }

    # 중요 키워드 (가중치 부여용)
    IMPORTANT_KEYWORDS = {
        "지원금", "보조금", "창업", "청년", "중소기업", "소상공인",
        "R&D", "연구개발", "특허", "수출", "고용", "채용", "교육",
        "컨설팅", "인증", "사업화", "기술", "혁신", "스타트업"
    }

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """
        텍스트를 토큰으로 분리

        Args:
            text: 입력 텍스트

        Returns:
            List[str]: 토큰 리스트
        """
        if not text:
            return []

        # 소문자 변환
        text = text.lower()

        # 특수문자 제거 (한글, 영문, 숫자만 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)

        # 공백으로 분리
        tokens = text.split()

        # 불용어 제거 및 최소 길이 필터링
        tokens = [
            token for token in tokens
            if token not in cls.STOPWORDS and len(token) > 1
        ]

        return tokens

    @classmethod
    def tokenize_with_ngrams(cls, text: str, n: int = 2) -> List[str]:
        """
        N-gram을 포함한 토큰화

        Args:
            text: 입력 텍스트
            n: N-gram 크기

        Returns:
            List[str]: 토큰 + N-gram 리스트
        """
        tokens = cls.tokenize(text)

        # N-gram 생성
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = "_".join(tokens[i:i+n])
            ngrams.append(ngram)

        return tokens + ngrams


class BM25Index:
    """
    BM25 인덱스

    문서 컬렉션에 대한 BM25 점수 계산
    """

    def __init__(self, config: BM25Config = None):
        """
        초기화

        Args:
            config: BM25 설정
        """
        self.config = config or BM25Config()
        self.tokenizer = KoreanTokenizer()

        # 인덱스 데이터
        self.doc_count = 0
        self.avg_doc_length = 0.0
        self.doc_lengths: Dict[int, int] = {}  # doc_id -> length
        self.doc_tokens: Dict[int, List[str]] = {}  # doc_id -> tokens
        self.term_doc_freqs: Dict[str, int] = {}  # term -> doc count containing term
        self.inverted_index: Dict[str, Dict[int, int]] = {}  # term -> {doc_id: term_freq}

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        문서 컬렉션으로 인덱스 구축

        Args:
            documents: 문서 리스트 [{"id": int, "content": str}, ...]
        """
        logger.info(f"Building BM25 index with {len(documents)} documents")

        self.doc_count = len(documents)
        total_length = 0

        for doc in documents:
            doc_id = doc.get("id") or doc.get("policy_id")
            content = doc.get("content", "")

            if not doc_id or not content:
                continue

            # 토큰화
            tokens = self.tokenizer.tokenize(content)

            # 문서 길이 저장
            self.doc_lengths[doc_id] = len(tokens)
            self.doc_tokens[doc_id] = tokens
            total_length += len(tokens)

            # Term frequency 계산
            term_freq = Counter(tokens)

            for term, freq in term_freq.items():
                # Inverted index 업데이트
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                self.inverted_index[term][doc_id] = freq

                # Document frequency 업데이트
                if term not in self.term_doc_freqs:
                    self.term_doc_freqs[term] = 0
                self.term_doc_freqs[term] += 1

        # 평균 문서 길이 계산
        if self.doc_count > 0:
            self.avg_doc_length = total_length / self.doc_count

        logger.info(
            f"BM25 index built: {self.doc_count} docs, "
            f"{len(self.inverted_index)} terms, "
            f"avg_length={self.avg_doc_length:.1f}"
        )

    def _compute_idf(self, term: str) -> float:
        """
        IDF (Inverse Document Frequency) 계산

        Args:
            term: 검색어

        Returns:
            float: IDF 값
        """
        doc_freq = self.term_doc_freqs.get(term, 0)

        if doc_freq == 0:
            return 0.0

        # IDF with smoothing
        idf = math.log(
            (self.doc_count - doc_freq + 0.5) /
            (doc_freq + 0.5) + 1
        )

        return max(idf, self.config.epsilon)

    def _compute_term_score(
        self,
        term: str,
        doc_id: int,
        term_freq: int
    ) -> float:
        """
        단일 term에 대한 BM25 점수 계산

        Args:
            term: 검색어
            doc_id: 문서 ID
            term_freq: 문서 내 term 빈도

        Returns:
            float: BM25 점수
        """
        idf = self._compute_idf(term)
        doc_length = self.doc_lengths.get(doc_id, 0)

        if doc_length == 0 or self.avg_doc_length == 0:
            return 0.0

        # BM25 score
        k1, b = self.config.k1, self.config.b

        numerator = term_freq * (k1 + 1)
        denominator = term_freq + k1 * (1 - b + b * doc_length / self.avg_doc_length)

        return idf * (numerator / denominator)

    def search(
        self,
        query: str,
        top_k: int = 20,
        min_score: float = 0.0
    ) -> List[Tuple[int, float]]:
        """
        쿼리로 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            min_score: 최소 점수

        Returns:
            List[Tuple[int, float]]: [(doc_id, score), ...] 점수 내림차순
        """
        query_tokens = self.tokenizer.tokenize(query)

        if not query_tokens:
            return []

        # 문서별 점수 계산
        doc_scores: Dict[int, float] = {}

        for term in query_tokens:
            if term not in self.inverted_index:
                continue

            # 중요 키워드 가중치
            term_weight = 1.5 if term in KoreanTokenizer.IMPORTANT_KEYWORDS else 1.0

            for doc_id, term_freq in self.inverted_index[term].items():
                score = self._compute_term_score(term, doc_id, term_freq) * term_weight

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = 0.0
                doc_scores[doc_id] += score

        # 점수 필터링 및 정렬
        results = [
            (doc_id, score)
            for doc_id, score in doc_scores.items()
            if score >= min_score
        ]
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def get_term_matches(
        self,
        query: str,
        doc_id: int
    ) -> List[str]:
        """
        쿼리와 문서 간 매칭된 term 반환

        Args:
            query: 검색 쿼리
            doc_id: 문서 ID

        Returns:
            List[str]: 매칭된 term 리스트
        """
        query_tokens = set(self.tokenizer.tokenize(query))
        doc_tokens = set(self.doc_tokens.get(doc_id, []))

        return list(query_tokens & doc_tokens)


class HybridSearcher:
    """
    하이브리드 검색기

    Dense (벡터) + Sparse (BM25) 검색 결합
    """

    def __init__(
        self,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        use_rrf: bool = True,
        rrf_k: int = 60
    ):
        """
        초기화

        Args:
            dense_weight: Dense 검색 가중치 (use_rrf=False 시)
            sparse_weight: Sparse 검색 가중치 (use_rrf=False 시)
            use_rrf: Reciprocal Rank Fusion 사용 여부
            rrf_k: RRF 파라미터 k
        """
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.use_rrf = use_rrf
        self.rrf_k = rrf_k
        self.bm25_index: Optional[BM25Index] = None

    def build_sparse_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Sparse 인덱스 구축

        Args:
            documents: 문서 리스트
        """
        self.bm25_index = BM25Index()
        self.bm25_index.build_index(documents)

    def combine_results(
        self,
        dense_results: List[Tuple[int, float]],
        sparse_results: List[Tuple[int, float]],
        normalize: bool = True
    ) -> List[Tuple[int, float, str]]:
        """
        Dense와 Sparse 결과 결합

        Args:
            dense_results: [(doc_id, score), ...] Dense 검색 결과
            sparse_results: [(doc_id, score), ...] Sparse 검색 결과
            normalize: 점수 정규화 여부

        Returns:
            List[Tuple[int, float, str]]: [(doc_id, combined_score, match_type), ...]
        """
        if self.use_rrf:
            return self._combine_rrf(dense_results, sparse_results)
        else:
            return self._combine_weighted(dense_results, sparse_results, normalize)

    def _combine_rrf(
        self,
        dense_results: List[Tuple[int, float]],
        sparse_results: List[Tuple[int, float]]
    ) -> List[Tuple[int, float, str]]:
        """
        Reciprocal Rank Fusion으로 결합

        RRF score = sum(1 / (k + rank))

        Args:
            dense_results: Dense 검색 결과
            sparse_results: Sparse 검색 결과

        Returns:
            List[Tuple[int, float, str]]: 결합된 결과
        """
        rrf_scores: Dict[int, float] = {}
        match_types: Dict[int, str] = {}
        k = self.rrf_k

        # Dense results RRF
        for rank, (doc_id, _) in enumerate(dense_results, 1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank)
            match_types[doc_id] = "dense"

        # Sparse results RRF
        for rank, (doc_id, _) in enumerate(sparse_results, 1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank)
            if doc_id in match_types:
                match_types[doc_id] = "hybrid"  # 둘 다 매칭
            else:
                match_types[doc_id] = "sparse"

        # 정렬
        results = [
            (doc_id, score, match_types[doc_id])
            for doc_id, score in rrf_scores.items()
        ]
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def _combine_weighted(
        self,
        dense_results: List[Tuple[int, float]],
        sparse_results: List[Tuple[int, float]],
        normalize: bool = True
    ) -> List[Tuple[int, float, str]]:
        """
        가중 평균으로 결합

        Args:
            dense_results: Dense 검색 결과
            sparse_results: Sparse 검색 결과
            normalize: 점수 정규화 여부

        Returns:
            List[Tuple[int, float, str]]: 결합된 결과
        """
        combined: Dict[int, Dict[str, float]] = {}

        # 정규화를 위한 최대값
        max_dense = max((s for _, s in dense_results), default=1.0) or 1.0
        max_sparse = max((s for _, s in sparse_results), default=1.0) or 1.0

        # Dense scores
        for doc_id, score in dense_results:
            if normalize:
                score = score / max_dense
            combined[doc_id] = {"dense": score, "sparse": 0.0}

        # Sparse scores
        for doc_id, score in sparse_results:
            if normalize:
                score = score / max_sparse
            if doc_id in combined:
                combined[doc_id]["sparse"] = score
            else:
                combined[doc_id] = {"dense": 0.0, "sparse": score}

        # 가중 평균 계산
        results = []
        for doc_id, scores in combined.items():
            weighted_score = (
                self.dense_weight * scores["dense"] +
                self.sparse_weight * scores["sparse"]
            )

            # Match type 결정
            if scores["dense"] > 0 and scores["sparse"] > 0:
                match_type = "hybrid"
            elif scores["dense"] > 0:
                match_type = "dense"
            else:
                match_type = "sparse"

            results.append((doc_id, weighted_score, match_type))

        results.sort(key=lambda x: x[1], reverse=True)
        return results


# 싱글톤 인스턴스
_hybrid_searcher: Optional[HybridSearcher] = None


def get_hybrid_searcher(
    dense_weight: float = 0.7,
    sparse_weight: float = 0.3,
    use_rrf: bool = True
) -> HybridSearcher:
    """
    HybridSearcher 싱글톤 인스턴스 반환

    Args:
        dense_weight: Dense 가중치
        sparse_weight: Sparse 가중치
        use_rrf: RRF 사용 여부

    Returns:
        HybridSearcher: 검색기 인스턴스
    """
    global _hybrid_searcher
    if _hybrid_searcher is None:
        _hybrid_searcher = HybridSearcher(
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            use_rrf=use_rrf
        )
    return _hybrid_searcher
