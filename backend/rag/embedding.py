#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding builder (minimal)
- Reads PMC articles from ./articles/{PMCID}/article.json
- Builds text-only embeddings using OpenAI text-embedding-3-small
- Saves FAISS index (cosine via L2 normalization) and metadata JSONL

Usage:
  # .env: OPENAI_API_KEY use
  python rag/embedding.py

Optional:
  python rag/embedding.py --articles articles --out data/index --model text-embedding-3-small --batch-size 256
"""
import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Dict

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Defaults
DEFAULT_ARTICLES_DIR = "articles"
DEFAULT_OUT_DIR = "data/index"
DEFAULT_MODEL = "text-embedding-3-small"
DEFAULT_BATCH = 256

# ------------- Corpus loading and chunking -------------
@dataclass
class Chunk:
    id: str
    pmcid: str
    title: str
    type: str  # "section" | "figure"
    section_title: Optional[str]
    figure_label: Optional[str]
    figure_caption: Optional[str]
    figure_tileshop: Optional[str]
    figure_image_urls: List[str]   # remote jpg/png urls
    text: str                      # embedding text

def _iter_article_jsons(articles_dir: Path) -> Iterable[Tuple[str, dict, Path]]:
    for pmcid_dir in sorted(articles_dir.iterdir()):
        if not pmcid_dir.is_dir():
            continue
        j = pmcid_dir / "article.json"
        if not j.exists():
            continue
        try:
            obj = json.loads(j.read_text(encoding="utf-8"))
        except Exception:
            continue
        pmcid = obj.get("pmcid") or pmcid_dir.name
        yield pmcid, obj, pmcid_dir

def _word_chunks(text: str, chunk_size: int = 220, overlap: int = 40) -> List[str]:
    words = (text or "").split()
    if not words:
        return []
    out: List[str] = []
    i, n = 0, len(words)
    while i < n:
        j = min(n, i + chunk_size)
        out.append(" ".join(words[i:j]))
        if j >= n:
            break
        i = max(i + chunk_size - overlap, i + 1)
    return out

def load_corpus(articles_dir: str) -> List[Chunk]:
    """
    - 섹션: Section.markdown을 워드 청킹
    - 피겨: caption 텍스트를 1개 청크로 사용
    - 이미지(URL/tileshop)는 메타데이터에만 저장(임베딩 미포함)
    """
    base = Path(articles_dir)
    chunks: List[Chunk] = []
    for pmcid, obj, _pmcid_dir in _iter_article_jsons(base):
        title = obj.get("title") or "Untitled"

        # Sections
        for si, sec in enumerate(obj.get("sections") or []):
            sec_title = (sec.get("title") or "").strip()
            md = (sec.get("markdown") or "").strip()
            for cj, piece in enumerate(_word_chunks(md)):
                if not piece.strip():
                    continue
                chunks.append(
                    Chunk(
                        id=f"{pmcid}::sec{si}::chunk{cj}",
                        pmcid=pmcid,
                        title=title,
                        type="section",
                        section_title=sec_title if sec_title else None,
                        figure_label=None,
                        figure_caption=None,
                        figure_tileshop=None,
                        figure_image_urls=[],
                        text=piece,
                    )
                )

        # Figures
        for fi, fig in enumerate(obj.get("figures") or []):
            caption = (fig.get("caption") or "").strip()
            if not caption:
                continue
            label = (fig.get("label") or "").strip() or None
            tileshop = fig.get("tileshop") or None
            # 새 크롤러는 images[].url, 과거 데이터는 images[].src 일 수 있어 둘 다 지원
            image_urls = []
            for im in (fig.get("images") or []):
                url = im.get("url") or im.get("src")
                if url:
                    image_urls.append(url)
            chunks.append(
                Chunk(
                    id=f"{pmcid}::fig{fi}",
                    pmcid=pmcid,
                    title=title,
                    type="figure",
                    section_title=None,
                    figure_label=label,
                    figure_caption=caption,
                    figure_tileshop=tileshop,
                    figure_image_urls=image_urls,
                    text=caption,
                )
            )
    return chunks

# ------------- OpenAI embedding -------------
def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    return (mat / norms).astype("float32")

def embed_texts_openai(client: OpenAI, model: str, texts: List[str], batch_size: int = DEFAULT_BATCH, max_retries: int = 5, retry_wait: float = 2.0) -> np.ndarray:
    vecs: List[List[float]] = []
    for i in tqdm(range(0, len(texts), batch_size), desc="embed"):
        batch = texts[i:i+batch_size]
        batch = [t if (t and t.strip()) else " " for t in batch]  # avoid empty input
        for attempt in range(1, max_retries + 1):
            try:
                resp = client.embeddings.create(model=model, input=batch)
                for d in resp.data:
                    vecs.append(d.embedding)
                break
            except Exception:
                if attempt >= max_retries:
                    raise
                time.sleep(retry_wait * attempt)
    arr = np.asarray(vecs, dtype="float32")
    return _l2_normalize(arr)

# ------------- Build and save -------------
def build_index(articles_dir: str, out_dir: str, model: str, batch_size: int) -> Dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    index_path = out / "faiss.index"
    meta_path = out / "meta.jsonl"

    print(f"[load] articles: {articles_dir}")
    chunks = load_corpus(articles_dir)
    if not chunks:
        raise SystemExit("No chunks found. Ensure articles/{PMCID}/article.json exists.")

    texts = [c.text for c in chunks]
    print(f"[openai] init")
    client = OpenAI()

    print(f"[embed] model={model}, n_texts={len(texts)}, batch={batch_size}")
    vecs = embed_texts_openai(client, model, texts, batch_size=batch_size)
    dim = vecs.shape[1]

    print(f"[faiss] build index dim={dim}")
    index = faiss.IndexFlatIP(dim)  # cosine via L2-normalized embeddings
    index.add(vecs)
    faiss.write_index(index, str(index_path))
    print(f"[ok] saved index: {index_path}")

    print(f"[meta] write: {meta_path}")
    with meta_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            rec = {
                "id": c.id,
                "pmcid": c.pmcid,
                "title": c.title,
                "type": c.type,
                "section_title": c.section_title,
                "figure_label": c.figure_label,
                "figure_caption": c.figure_caption,
                "figure_tileshop": c.figure_tileshop,
                "figure_image_urls": c.figure_image_urls,  # UI에서 바로 표시 가능
                "text": c.text,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[done]")
    return {"index": str(index_path), "meta": str(meta_path)}

def main():
    load_dotenv()  # reads .env with OPENAI_API_KEY
    ap = argparse.ArgumentParser(description="Build text embeddings with OpenAI (minimal CLI).")
    ap.add_argument("--articles", default=DEFAULT_ARTICLES_DIR, help="Articles root directory (default: articles)")
    ap.add_argument("--out", default=DEFAULT_OUT_DIR, help="Output directory for index and metadata (default: data/index)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI embedding model (default: text-embedding-3-small)")
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH, help="Batch size (default: 256)")
    args = ap.parse_args()
    build_index(args.articles, args.out, args.model, args.batch_size)

if __name__ == "__main__":
    main()