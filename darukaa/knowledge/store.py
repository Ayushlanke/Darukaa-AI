import hashlib
import math
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from rank_bm25 import BM25Okapi

from darukaa import config
from darukaa.knowledge.ingest import Chunk, indexed_text, is_fao_or_ipcc

RRF_K = 60  # research.md §2.5 / Cormack et al. (2009) — de facto default RRF constant.


class LightweightEmbeddingFunction(EmbeddingFunction[Documents]):
    """Memory-efficient dense embedding function for ChromaDB.
    Uses n-gram hashed feature projection with L2 normalization to keep RAM < 120MB
    (preventing ONNX Runtime OOM on memory-constrained 512MB hosting like Render free tier)
    while providing dense vector similarity for hybrid RRF retrieval."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def name(self) -> str:
        return "darukaa_lightweight_dense"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for doc in input:
            vec = [0.0] * self.dim
            tokens = doc.lower().split()
            for t in tokens:
                idx = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16) % self.dim
                vec[idx] += 1.0
            for i in range(len(tokens) - 1):
                bg = f"{tokens[i]}_{tokens[i+1]}"
                idx = int(hashlib.md5(bg.encode("utf-8")).hexdigest(), 16) % self.dim
                vec[idx] += 0.5
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            embeddings.append([x / norm for x in vec])
        return embeddings


class EvidenceStore:
    """Hybrid BM25 + dense retrieval over the evidence corpus (architecture.md §4).
    No reranker (D12) and no LLM self-query step (D13) — filtering and fusion are plain code."""

    def __init__(self, chunks: list[Chunk], persist: bool = True):
        self.chunks = {c.id: c for c in chunks}
        ids = list(self.chunks.keys())
        self._bm25_index = {cid: i for i, cid in enumerate(ids)}
        self._bm25 = BM25Okapi([indexed_text(c).lower().split() for c in chunks])

        client = (
            chromadb.PersistentClient(path=str(config.CHROMA_DIR))
            if persist
            else chromadb.EphemeralClient()
        )
        self._ef = LightweightEmbeddingFunction()
        self._collection = client.get_or_create_collection("evidence_v2", embedding_function=self._ef)
        if self._collection.count() == 0 and chunks:
            self._collection.add(
                ids=ids,
                documents=[indexed_text(c) for c in chunks],
                metadatas=[{"topic": c.topic} for c in chunks],
            )

    def retrieve(self, query: str, topic: str, top_k: int = 5) -> list:
        topic_ids = [cid for cid, c in self.chunks.items() if c.topic == topic]
        if not topic_ids:
            return []

        bm25_scores = self._bm25.get_scores(query.lower().split())
        bm25_ranking = sorted(topic_ids, key=lambda cid: bm25_scores[self._bm25_index[cid]], reverse=True)

        dense = self._collection.query(query_texts=[query], n_results=len(topic_ids), where={"topic": topic})
        dense_ranking = dense["ids"][0]

        rrf_scores: dict = {}
        for rank, cid in enumerate(bm25_ranking):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1 / (RRF_K + rank)
        for rank, cid in enumerate(dense_ranking):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1 / (RRF_K + rank)

        fused_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)
        top = [self.chunks[cid] for cid in fused_ids[:top_k]]

        # D21: surface a relevant FAO/IPCC chunk alongside the primary citation when one
        # exists for this topic, even if it ranked below top_k.
        if not any(is_fao_or_ipcc(c) for c in top):
            extra = next((self.chunks[cid] for cid in fused_ids if is_fao_or_ipcc(self.chunks[cid])), None)
            if extra:
                top.append(extra)
        return top
