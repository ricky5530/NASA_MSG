#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Reformer for scientific RAG (synonym expansion removed)
- LLM-based multi-query generation (LangChain)
- HyDE: Hypothetical Document Embeddings generator

Env:
  OPENAI_API_KEY
"""
from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

DEFAULT_CHAT_MODEL = "gpt-4o-mini"

@dataclass
class ReformedQueries:
    rule_expanded: List[str]
    llm_generated: List[str]
    hyde_document: Optional[str]


class QueryReformer:
    def __init__(self, chat_model: Optional[str] = None, temperature: float = 0.2):
        model = chat_model or DEFAULT_CHAT_MODEL
        self.llm = ChatOpenAI(model=model, temperature=temperature)

        self.multi_query_prompt = PromptTemplate(
            input_variables=["question", "n"],
            template=(
                "You are assisting literature search in NASA biosciences.\n"
                "Given the question, generate {n} diverse, concise search queries that capture:\n"
                "- Scientific synonyms, related pathways, and organism/model variants\n"
                "- Outcomes/phenotypes, exposure context (microgravity, radiation), and mission terms (ISS)\n"
                "- Keep each query < 16 words. Do NOT number them. One per line.\n\n"
                "- IMPORTANT: Return all queries in English regardless of the question language.\n\n"  # Force multi-query outputs to English
                "Question: {question}\n"
                "Queries:"
            ),
        )

        self.hyde_prompt = PromptTemplate(
            input_variables=["question"],
            template=(
                "Write a short factual abstract (120-200 words) that could appear in a NASA bioscience paper, "
                "summarizing likely findings that directly address the question below. "
                "Focus on RESULTS-like content and technical terms, avoid speculation.\n\n"
                "Write the abstract in English regardless of the question language.\n\n"  # Force HyDE abstract to be in English
                "Question: {question}\n\n"
                "Abstract:"
            ),
        )

    def generate_multi_queries_llm(self, question: str, n: int = 6) -> List[str]:
        prompt = self.multi_query_prompt.format(question=question, n=n)
        resp = self.llm.invoke(prompt)
        text = (resp.content or "").strip()
        # Strip common bullet characters and whitespace; keep order and uniqueness by simple scan
        seen = set()
        out: List[str] = []
        for ln in text.splitlines():
            q = ln.strip(" -•\t").strip()
            k = " ".join(q.lower().split())
            if q and k not in seen:
                seen.add(k)
                out.append(q)
                if len(out) >= n:
                    break
        return out

    def generate_hyde_document(self, question: str) -> str:
        prompt = self.hyde_prompt.format(question=question)
        resp = self.llm.invoke(prompt)
        return (resp.content or "").strip()

    def reform(self, question: str, n_llm: int = 6, use_hyde: bool = True) -> ReformedQueries:
        # No rule-based synonym expansion (intentionally removed)
        rule_qs: List[str] = []
        try:
            llm_qs = self.generate_multi_queries_llm(question, n=n_llm)
        except Exception:
            llm_qs = []
        hyde_doc = None
        if use_hyde:
            try:
                hyde_doc = self.generate_hyde_document(question)
            except Exception:
                hyde_doc = None
        return ReformedQueries(rule_expanded=rule_qs, llm_generated=llm_qs, hyde_document=hyde_doc)