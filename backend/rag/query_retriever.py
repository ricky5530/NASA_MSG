#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain BaseRetriever over existing FAISS index + meta.jsonl produced by rag/embedding.py

- Loads FAISS index from data/index/faiss.index
- Loads metadata from data/index/meta.jsonl (one JSON per line)
- Embeds queries with OpenAIEmbeddings (must match the model used for the index)
- Uses cosine similarity via L2-normalized vectors

Env:
  OPENAI_API_KEY
"""
from __future__ import annotations
from typing import List, Tuple, Dict, Any
import json
from pathlib import Path

import numpy as np
import faiss

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai.embeddings import OpenAIEmbeddings
from pydantic import PrivateAttr

DEFAULT_INDEX = Path("data/index/faiss.index")
DEFAULT_META = Path("data/index/meta.jsonl")
DEFAULT_EMBED = "text-embedding-3-small"


def _read_meta(meta_path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with meta_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(vec, axis=1, keepdims=True) + 1e-12
    return (vec / n).astype("float32")


class FAISSJsonlStore:
    def __init__(self, index_path: Path = DEFAULT_INDEX, meta_path: Path = DEFAULT_META):
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"meta.jsonl not found: {meta_path}")

        self.index = faiss.read_index(str(index_path))
        self.meta: List[Dict[str, Any]] = _read_meta(meta_path)

    def search(self, qvec: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        D, I = self.index.search(qvec, top_k)
        return D[0], I[0]

    def get_item(self, idx: int) -> Dict[str, Any]:
        return self.meta[idx]


class FAISSJsonlRetriever(BaseRetriever):
    # Pydantic model fields (serializable)
    index_path: str
    meta_path: str
    embed_model: str = DEFAULT_EMBED
    top_k: int = 5

    # Non-serializable runtime attributes
    _store: FAISSJsonlStore = PrivateAttr()
    _embeddings: OpenAIEmbeddings = PrivateAttr()

    def __init__(
        self,
        index_path: Path = DEFAULT_INDEX,
        meta_path: Path = DEFAULT_META,
        embed_model: str = DEFAULT_EMBED,
        top_k: int = 5,
    ):
        # Initialize pydantic fields via super().__init__
        super().__init__(
            index_path=str(index_path),
            meta_path=str(meta_path),
            embed_model=embed_model,
            top_k=top_k,
        )
        # Initialize runtime attributes
        self._store = FAISSJsonlStore(Path(self.index_path), Path(self.meta_path))
        self._embeddings = OpenAIEmbeddings(model=self.embed_model)

    def _embed_query(self, query: str) -> np.ndarray:
        vec = np.asarray([self._embeddings.embed_query(query)], dtype="float32")
        return _l2_normalize(vec)

    def _build_doc(self, item: Dict[str, Any]) -> Document:
        text = item.get("text") or ""
        meta = dict(item)
        meta.pop("text", None)
        pmcid = meta.get("pmcid")
        if pmcid and "url" not in meta:
            meta["url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
        return Document(page_content=text, metadata=meta)

    # In langchain-core, override the protected method
    def _get_relevant_documents(self, query: str) -> List[Document]:
        qvec = self._embed_query(query)
        _D, I = self._store.search(qvec, self.top_k)
        docs: List[Document] = []
        for idx in I:
            if int(idx) < 0:
                continue
            item = self._store.get_item(int(idx))
            docs.append(self._build_doc(item))
        return docs

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        # Simple sync wrapper
        return self._get_relevant_documents(query)


def reciprocal_rank_fusion(
    rankings: List[List[Document]],
    k: int = 60,
    top_k: int = 8,
    doc_id_key: str = "id",
) -> List[Document]:
    """
    RRF fuse multiple ranked lists.
    Identity of a Document is determined by metadata[doc_id_key] if present, else by (pmcid, chunk id).
    """
    def doc_key(d: Document) -> str:
        meta = d.metadata or {}
        if doc_id_key in meta:
            return str(meta[doc_id_key])
        pmcid = meta.get("pmcid", "")
        cid = meta.get("id", "")
        return f"{pmcid}::{cid}"

    scores: Dict[str, float] = {}
    by_id: Dict[str, Document] = {}
    for ranking in rankings:
        for rank, d in enumerate(ranking):
            key = doc_key(d)
            by_id[key] = d
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1.0)
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    fused: List[Document] = [by_id[k] for k, _ in ordered[:top_k]]
    return fused