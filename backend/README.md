# Backend

FastAPI backend that serves the Space Biology Knowledge Engine RAG API. This layer wires HTTP endpoints to the RAG pipeline in `backend/rag` and returns chat-ready Markdown.

If you're looking for RAG internals (index build, prompts, pipeline design), see `backend/rag/README.md`.

---

## What this service does

Exposes HTTP endpoints for:
- Generating a Markdown answer grounded in PMC literature via RAG (`POST /rag/md`)
- Lightweight dashboard summaries and recent activity
- Health checks and a simple root status

Internally it calls `rag/query_markdown.py → run_query()` which performs: query reform (English), FAISS retrieval, RRF fusion, figure collection, and answer generation with PMCID citations.

---

## Folder layout (backend/)

- `main.py` – FastAPI app with routes
- `requirements.txt` – Python dependencies
- `.env.example` – sample environment file
- `data/` – runtime data
  - `index/` – FAISS artifacts (required at runtime)
    - `faiss.index`
    - `meta.jsonl`
  - `raw/` – optional raw provenance sources (CSV)
- `rag/` – RAG implementation (see its README for details)

---

## API endpoints

Base URL examples:
- Local: `http://localhost:8001`

### GET `/` – status
Returns service status and basic features list.

### GET `/health` – health check
Returns `{ "ok": true }` if the server is up.

### POST `/user/session/start` – start a lightweight session
Returns a generated `user_id` and `session_id`. No database dependency.

### POST `/rag/md` – RAG answer (Markdown)

Request body (JSON):

```json
{
  "question": "How to measure electrical impedance?",
  "include_sources": true,
  "include_figures": true,
  "fig_max_images": 2,
  "fig_caption_max_chars": 0
}
```

Response: `text/markdown` string containing sections:
- `# Answer` – localized to the question language, with PMCID citations like `[PMC1234567]`
- `## Sources` – only the PMCIDs actually cited in the answer (hyperlinked)
- `## Figures` – optional, figure info and thumbnails (if available)
- `> #### Topic : ...` – short English topic tag

### GET `/dashboard/summary`
Aggregated counters for messages, languages, topics, and average latency.

### GET `/dashboard/activity`
Recent activity list (timestamp, language, topic, preview).