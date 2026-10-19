"""
Hybrid Semantic Retrieval Engine.

Combines BM25 keyword matching (for exact ticker symbols, numbers, accounting terms)
with Dense Vector Embeddings using Reciprocal Rank Fusion (RRF).
"""

from collections import Counter
import hashlib
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from packages.retrieval.chunker import DocumentChunk


def tokenize(text: str) -> List[str]:
    """Tokenize into alphanumeric words."""
    return re.findall(r"\b[A-Za-z0-9\$\%]+\b", text.lower())


def generate_pseudo_dense_embedding(text: str, dim: int = 64) -> List[float]:
    """
    Generates a deterministic normalized dense embedding vector from text.
    In production, can be replaced by Gemini / OpenAI embedding API calls.
    """
    tokens = tokenize(text)
    vec = [0.0] * dim
    for t in tokens:
        # Hash token to dimension indices
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        idx1 = h % dim
        idx2 = (h >> 16) % dim
        vec[idx1] += 1.0
        vec[idx2] += 0.5

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    return sum(a * b for a, b in zip(v1, v2))


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len: Dict[str, int] = {}
        self.doc_freq: Dict[str, int] = Counter()
        self.term_freqs: Dict[str, Counter] = {}
        self.avg_len: float = 0.0
        self.num_docs: int = 0

    def index_document(self, doc_id: str, tokens: List[str]):
        self.doc_len[doc_id] = len(tokens)
        tf = Counter(tokens)
        self.term_freqs[doc_id] = tf
        for term in tf:
            self.doc_freq[term] += 1
        self.num_docs += 1
        self.avg_len = sum(self.doc_len.values()) / self.num_docs

    def score(self, query_tokens: List[str], doc_id: str) -> float:
        if doc_id not in self.term_freqs:
            return 0.0
        score = 0.0
        tf_dict = self.term_freqs[doc_id]
        dl = self.doc_len[doc_id]

        for t in query_tokens:
            if t not in tf_dict:
                continue
            df = self.doc_freq.get(t, 0)
            idf = math.log(1.0 + (self.num_docs - df + 0.5) / (df + 0.5))
            tf = tf_dict[t]
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (dl / max(1.0, self.avg_len)))
            score += idf * (numerator / denominator)
        return score


class HybridRetrievalEngine:
    def __init__(self):
        self.chunks: Dict[str, DocumentChunk] = {}
        self.embeddings: Dict[str, List[float]] = {}
        self.bm25 = BM25Index()

    def add_chunks(self, chunks: List[DocumentChunk]):
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            tokens = tokenize(chunk.text)
            self.bm25.index_document(chunk.id, tokens)
            self.embeddings[chunk.id] = generate_pseudo_dense_embedding(chunk.text)

    def index_chunks(self, chunks: List[DocumentChunk]):
        """Alias for add_chunks."""
        self.add_chunks(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Executes hybrid search combining dense semantic similarity and BM25
        via Reciprocal Rank Fusion (RRF, k=60).
        """
        if not self.chunks:
            return []

        query_tokens = tokenize(query)
        query_embedding = generate_pseudo_dense_embedding(query)

        candidates = [
            cid for cid, ch in self.chunks.items()
            if (document_id is None or ch.document_id == document_id)
        ]
        if not candidates:
            return []

        # 1. Dense Scoring
        dense_scores = [
            (cid, cosine_similarity(query_embedding, self.embeddings[cid]))
            for cid in candidates
        ]
        dense_scores.sort(key=lambda x: x[1], reverse=True)
        dense_ranks = {cid: rank for rank, (cid, _) in enumerate(dense_scores, start=1)}

        # 2. BM25 Scoring
        bm25_scores = [
            (cid, self.bm25.score(query_tokens, cid))
            for cid in candidates
        ]
        bm25_scores.sort(key=lambda x: x[1], reverse=True)
        bm25_ranks = {cid: rank for rank, (cid, _) in enumerate(bm25_scores, start=1)}

        # 3. Reciprocal Rank Fusion
        rrf_scores: List[Tuple[str, float]] = []
        for cid in candidates:
            r_dense = dense_ranks.get(cid, 1000)
            r_bm25 = bm25_ranks.get(cid, 1000)
            score = (1.0 / (60.0 + r_dense)) + (1.0 / (60.0 + r_bm25))
            rrf_scores.append((cid, score))

        rrf_scores.sort(key=lambda x: x[1], reverse=True)

        results: List[Tuple[DocumentChunk, float]] = []
        for cid, score in rrf_scores[:top_k]:
            results.append((self.chunks[cid], score))

        return results


_GLOBAL_RETRIEVAL_ENGINE: Optional[HybridRetrievalEngine] = None


def get_retrieval_engine() -> HybridRetrievalEngine:
    global _GLOBAL_RETRIEVAL_ENGINE
    if _GLOBAL_RETRIEVAL_ENGINE is None:
        _GLOBAL_RETRIEVAL_ENGINE = HybridRetrievalEngine()
    return _GLOBAL_RETRIEVAL_ENGINE
