#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end scientific RAG query pipeline:
- Query reformation (optional; rules + multi-query + HyDE if available)
- Retrieval per query (FAISS index from scripts/embedding.py)
- RRF fusion
- Figure attachment collection (direct figure chunks + 'Figure N' resolution via article.json)
- Answer generation with strict citation style [PMCID]
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document

from query_retriever import FAISSJsonlRetriever, reciprocal_rank_fusion
from query_figure_utils import collect_figures_for_docs
from query_reformer import QueryReformer

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = BASE_DIR / "data" / "index" / "faiss.index"
DEFAULT_META = BASE_DIR / "data" / "index" / "meta.jsonl"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_CHAT_MODEL = "gpt-4o-mini"

ANSWER_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a scientific assistant for NASA bioscience literature.\n"
        "Answer ONLY with information supported in the CONTEXT. If unclear or not supported, say you are unsure.\n\n"
        "Citations policy (critical for hyperlinking):\n"
        "- Always cite using actual PMC identifiers from the CONTEXT in the exact format [PMC1234567].\n"
        "- Never write placeholders like [PMCID], [PMID], or DOIs. Use uppercase 'PMC' with digits only, no spaces.\n"
        "- Place citations at the end of each factual sentence, or at the end of a short claim block that spans multiple closely related sentences.\n"
        "- When multiple studies support a claim, include multiple citations as separate brackets, e.g., [PMC1234567], [PMC7654321].\n"
        "- Do not fabricate citations; only use PMCIDs present in the CONTEXT. If none apply, say you are unsure.\n\n"
        "Style and structure (cohesive, chatbot tone):\n"
        "- Use Markdown.\n"
        "- Start with a brief executive summary (1–2 sentences) giving the main takeaway (one citation at the end of the paragraph is sufficient).\n"
        "- Then provide a short bulleted list of key findings (3–6 bullets max). Keep each bullet to ≤2 sentences and cite appropriately.\n"
        "- Do not repeat the question. Do not merge multiple list items onto one line.\n\n"
        "Question: {question}\n"
        "CONTEXT:\n{context}\n\n"
        "Answer:"
    ),
)

@dataclass
class SourceItem:
    pmcid: str
    title: str
    url: str

@dataclass
class FigureItem:
    pmcid: str
    label: Optional[str]
    caption: Optional[str]
    tileshop: Optional[str]
    images: List[Dict[str, str]]

@dataclass
class QueryResult:
    question: str
    answer: str
    sources: List[SourceItem]
    figures: List[FigureItem]
    topic: str

def _doc_to_dict(d: Document) -> Dict[str, Any]:
    return {
        "page_content": d.page_content,
        "metadata": dict(d.metadata or {}),
    }

def _build_context(docs: List[Document], max_chars: int = 12000) -> str:
    parts: List[str] = []
    used = 0
    for d in docs:
        m = d.metadata or {}
        pmcid = m.get("pmcid", "PMCID?")
        title = (m.get("title") or "")[:160]
        sec = m.get("section_title") or m.get("type") or ""
        header = f"[{pmcid}] {title} - {sec}".strip()
        body = (d.page_content or "").strip()
        chunk = f"{header}\n{body}\n"
        if used + len(chunk) > max_chars:
            break
        parts.append(chunk)
        used += len(chunk)
    return "\n---\n".join(parts)

def _format_sources(docs: List[Document]) -> List[SourceItem]:
    out: List[SourceItem] = []
    seen = set()
    for d in docs:
        m = d.metadata or {}
        pmcid = m.get("pmcid")
        if not pmcid or pmcid in seen:
            continue
        seen.add(pmcid)
        title = (m.get("title") or "")[:200]
        url = m.get("url") or f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
        out.append(SourceItem(pmcid=pmcid, title=title, url=url))
    return out

class RAGPipeline:
    def __init__(
        self,
        index_path: Path = DEFAULT_INDEX,
        meta_path: Path = DEFAULT_META,
        embed_model: str = DEFAULT_EMBED_MODEL,
        chat_model: str = DEFAULT_CHAT_MODEL,
        k_per_query: int = 6,
        top_k_final: int = 6,
        enable_reform: bool = True,       # toggle query reformer usage
        use_hyde: bool = True,
        n_llm_rewrites: int = 6,
    ):
        self.retriever = FAISSJsonlRetriever(
            index_path=index_path,
            meta_path=meta_path,
            embed_model=embed_model,
            top_k=k_per_query,
        )
        self.enable_reform = enable_reform and (QueryReformer is not None)
        self.reformer = QueryReformer(chat_model=chat_model) if self.enable_reform else None
        self.use_hyde = use_hyde if self.enable_reform else False
        self.n_llm_rewrites = n_llm_rewrites if self.enable_reform else 0
        self.llm = ChatOpenAI(model=chat_model, temperature=0.2)
        self.top_k_final = top_k_final

    def run(self, question: str) -> QueryResult:
        # 1) Build sub-queries
        if self.reformer:
            rq = self.reformer.reform(question, n_llm=self.n_llm_rewrites, use_hyde=self.use_hyde)
            subqueries: List[str] = []
            subqueries.extend(rq.rule_expanded or [])
            subqueries.extend(rq.llm_generated or [])
            hyde_text = rq.hyde_document
        else:
            subqueries = [question]
            hyde_text = None

        # Combine queries for batch retrieval
        queries: List[str] = list(subqueries)
        if hyde_text:
            queries.append(hyde_text)

        # 2) Retrieve per sub-query using Runnable API (.batch)
        # This replaces deprecated get_relevant_documents calls.
        rankings: List[List[Document]] = self.retriever.batch(queries)

        # Guard: if nothing retrieved at all
        if not any(rankings):
            return QueryResult(
                question=question,
                answer="I'm unsure. I couldn't retrieve supporting evidence from the corpus.",
                sources=[],
                figures=[],
                topic="",
            )

        # 3) RRF fuse
        fused = reciprocal_rank_fusion(rankings, k=60, top_k=self.top_k_final)

        # 4) Build context
        context = _build_context(fused)

        # 5) Generate answer
        prompt = ANSWER_PROMPT.format(context=context, question=question)
        ans_msg = self.llm.invoke(prompt)
        answer = (ans_msg.content or "").strip()

        # 6) Collect sources and figures
        docs_dict = [_doc_to_dict(d) for d in fused]
        figures_raw = collect_figures_for_docs(docs_dict)
        figures = [
            FigureItem(
                pmcid=f.get("pmcid"),
                label=f.get("label"),
                caption=f.get("caption"),
                tileshop=f.get("tileshop"),
                images=f.get("images") or [],
            ) for f in figures_raw
        ]
        sources = _format_sources(fused)

        # 7) Summarize topic (1-2 words, Title Case) unless unanswerable
        unans_markers = ["i'm unsure", "i am unsure", "unsure", "not sure", "cannot answer", "couldn't retrieve"]
        is_unanswerable = (not answer) or any(m in answer.lower() for m in unans_markers)
        if is_unanswerable:
            topic = ""
        else:
            try:
                topic_prompt = (
                    "You will receive the user's Question and the model Answer."
                    " Summarize the main topic in 1-2 words only.\n"
                    "Guidelines:\n"
                    "- PRIORITIZE the core subject of the Question; use the Answer to refine specificity.\n"
                    "- If the Question and Answer diverge, prefer the Question’s domain term.\n"
                    "- Output ONLY the topic text (no quotes, no punctuation, no extra words).\n"
                    "- ALWAYS output in English (even if the Question is not in English).\n"
                    "- Use Title Case in English (e.g., 'Microgravity', 'Immune System').\n"
                    "- If unclear, output 'General'.\n\n"
                    f"Question:\n{question}\n\nAnswer:\n{answer}\n\nTopic:"
                )
                topic_msg = self.llm.invoke(topic_prompt)
                raw_topic = (topic_msg.content or "").strip()
                cleaned = " ".join(raw_topic.split())
                tokens = cleaned.split()
                topic = " ".join(tokens[:2]) if tokens else "General"
                if not topic:
                    topic = "General"
            except Exception:
                topic = "General"

        return QueryResult(
            question=question,
            answer=answer,
            sources=sources,
            figures=figures,
            topic=topic,
        )

def run_query(
    question: str,
    index_path: Path = DEFAULT_INDEX,
    meta_path: Path = DEFAULT_META,
    embed_model: str = DEFAULT_EMBED_MODEL,
    chat_model: str = DEFAULT_CHAT_MODEL,
    k_per_query: int = 6,
    top_k_final: int = 6,
    enable_reform: bool = True,
    use_hyde: bool = True,
    n_llm_rewrites: int = 6,
) -> Dict[str, Any]:
    pipe = RAGPipeline(
        index_path=index_path,
        meta_path=meta_path,
        embed_model=embed_model,
        chat_model=chat_model,
        k_per_query=k_per_query,
        top_k_final=top_k_final,
        enable_reform=enable_reform,
        use_hyde=use_hyde,
        n_llm_rewrites=n_llm_rewrites,
    )
    res = pipe.run(question)
    return {
        "question": res.question,
        "answer": res.answer,
        "sources": [asdict(s) for s in res.sources],
        "figures": [asdict(f) for f in res.figures],
        "topic": res.topic,
    }