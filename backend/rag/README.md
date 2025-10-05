# NASA_MSG RAG (backend/rag)

Retrieval-Augmented Generation for scientific literature (PubMed Central, PMC). Built for hackathons: minimal setup, one-command smoke tests, clear citations.

Key features
- OpenAI embeddings (text-embedding-3-small) + FAISS search
- Query reforming: Multi-Query and HyDE (hypothetical doc)
- Reciprocal Rank Fusion (RRF) for robust ranking
- Section text + figure captions retrieval; resolves “Figure N” references and collects figure metadata
- Strict citations with PMCIDs only: [PMC1234567]
- Multilingual UX: retrieval in English, final answer in the user’s language

Note: Index files default to `backend/data/index/{faiss.index, meta.jsonl}`.

---

## Layout

- `crawl_pmc.py` – optional script to fetch article.json per PMCID
- `embedding.py` – builds embeddings from article JSON; saves FAISS index + meta JSONL
- `query_retriever.py` – FAISS + JSONL retriever
- `query_reformer.py` – LLM-based multi-query and HyDE (forces English for retrieval)
- `query_figure_utils.py` – figure collection and “Figure N” resolution
- `query_pipeline.py` – end-to-end: reform → retrieve → RRF → answer
- `query_markdown.py` – small helper to get Markdown output for quick tests

Data files
- `../data/index/faiss.index` – FAISS index
- `../data/index/meta.jsonl` – metadata per chunk (one JSON per line)

---

## Setup

Prereqs
- Python 3.10+
- OpenAI API key (via .env)

Create `backend/.env`:

```
OPENAI_API_KEY=sk-...
```

Install deps (WSL/bash):

```bash
cd NASA_MSG/backend
pip install -r requirements.txt
```

---

## Build the index (optional)

If `backend/data/index/` already exists, you can skip. To rebuild you need `articles/{PMCID}/article.json`.

```bash
cd NASA_MSG/backend
python rag/embedding.py \
  --articles articles \
  --out data/index \
  --model text-embedding-3-small \
  --batch-size 256
```

Outputs
- `data/index/faiss.index`
- `data/index/meta.jsonl`

`meta.jsonl` schema (per line):
- `id`: chunk id (e.g., "PMC12345::sec0::chunk1" or "PMC12345::fig2")
- `pmcid`: PMCID
- `title`: article title
- `type`: `section` | `figure`
- `section_title`: if any
- `figure_label`: e.g., "Figure 2"
- `figure_caption`: caption text
- `figure_tileshop`: tileshop URL (optional)
- `figure_image_urls`: array of image URLs
- `text`: text used for embedding (word-chunked section or caption)

---

## Quick try (Question → Markdown)

Smoke test multilingual behavior (English retrieval, non-English answer):

```bash
cd NASA_MSG/backend
python -c "from rag.query_markdown import query_to_markdown; print(query_to_markdown('미세중력에서 골밀도 변화는?', include_sources=True, include_figures=False))"
```

Expected
- QueryReformer generates English multi-queries/HyDE for retrieval
- Final answer is in the question language (Korean in this example) with sentence-level PMC citations

---

## Multilingual behavior

- Retrieval: prompts in `query_reformer.py` force English for multi-queries and HyDE (stable embedding).
- Answering: `ANSWER_PROMPT` in `query_pipeline.py` includes:

```
Respond in the same language as the Question. If the Question is not in English, translate the English CONTEXT facts faithfully into that language. Do not translate PMCIDs.
```

If the model still replies in English
- Check top-level system/instruction prompts don’t force English
- Ensure the above localization line exists in `ANSWER_PROMPT`
- Ensure the user question string is passed unchanged to the answer prompt

---

## Pipeline at a glance

1) Reform (optional)
   - LLM multi-queries + HyDE (English)
2) Retrieve
   - OpenAI embeddings → FAISS KNN per query
3) Fuse
   - RRF across query runs → final top_k
4) Figures
   - Include figure-caption chunks and resolve "Figure N" via article.json
5) Answer
   - Context-grounded, sentence-level PMC citations, response in user language

---

## Script notes

- `embedding.py`
  - Batch OpenAI embeddings, L2-normalize; FAISS IP ≈ cosine
  - Writes index and meta to `data/index/`

- `query_retriever.py`
  - `FAISSJsonlRetriever` loads `faiss.index` + `meta.jsonl`, embeds queries via `OpenAIEmbeddings`
  - Returns `langchain_core.documents.Document[]`

- `query_reformer.py`
  - `generate_multi_queries_llm`, `generate_hyde_document`, `reform`
  - Prompts enforce English outputs for retrieval consistency

- `query_pipeline.py`
  - Reform → retrieve → RRF → figure attach → answer (with localization rule)

- `query_markdown.py`
  - Simple helper to get a Markdown string for demos/tests

---

## Tips

- Models: defaults are `text-embedding-3-small` and `gpt-4o-mini`; uses `OPENAI_API_KEY` from `.env`.
- Performance: tune `--batch-size` for embeddings; includes simple retry logic.
- Citations: only PMCIDs allowed. Do not fabricate. If unsupported → acknowledge uncertainty.
- Figures: `figure_image_urls` can be rendered directly by the frontend.

