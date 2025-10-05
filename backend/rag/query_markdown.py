#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown for the new RAG pipeline with figure extraction (Markdown output)
- Only show cited PMCIDs in Sources
- Robust linking for citations in the answer:
  * [PMC12345] / [pmc 12345] / [[PMC12345]] (no link) / [PMC12345, PMC67890]
- Figures with [[Tileshop]] hyperlink
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

from query_pipeline import run_query

BASE_DIR = Path(__file__).resolve().parents[1]
INDEX_PATH = BASE_DIR / "data" / "index" / "faiss.index"
META_PATH = BASE_DIR / "data" / "index" / "meta.jsonl"

# --- Citation patterns (case-insensitive, tolerant of spaces) ---
# e.g., [PMC1234567] or [pmc 1234567]
PMC_SINGLE_BRACKET_RE = re.compile(r"\[\s*(pmc\s*\d+)\s*\]", re.I)
# e.g., [[PMC1234567]] NOT followed by '(' (so it's not already a link)
PMC_DOUBLE_BRACKET_NOLINK_RE = re.compile(r"\[\[\s*(pmc\s*\d+)\s*\]\](?!\()", re.I)
# e.g., [PMC123, PMC456, pmc 789]
PMC_MULTI_BRACKET_RE = re.compile(r"\[\s*((?:pmc\s*\d+\s*,\s*)+pmc\s*\d+)\s*\]", re.I)

def _normalize_pmcid(raw: str) -> str:
    """
    Normalize to 'PMC########' (uppercase, no spaces).
    Accepts inputs like 'pmc123', 'pmc 123', '123' (adds PMC).
    """
    if not raw:
        return ""
    t = raw.strip().upper().replace(" ", "")
    # ensure startswith PMC
    if t.startswith("PMC"):
        digits = re.sub(r"\D", "", t[3:])
        return f"PMC{digits}" if digits else ""
    # if only digits given
    digits = re.sub(r"\D", "", t)
    return f"PMC{digits}" if digits else ""

def _build_pmc_url_map(sources: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    sources: [{pmcid, title, url}]
    return: { normalized PMCID: url }
    """
    m: Dict[str, str] = {}
    for s in sources or []:
        pmcid_raw = s.get("pmcid")
        pmc = _normalize_pmcid(str(pmcid_raw) if pmcid_raw is not None else "")
        if not pmc:
            continue
        url = s.get("url") or f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/"
        m[pmc] = url
    return m

def _extract_cited_pmcids(answer: str) -> Set[str]:
    """
    Extract PMCIDs from answer, covering single/double/multi bracket styles.
    """
    if not answer:
        return set()
    ids: Set[str] = set()
    # [[PMC...]] without link
    for m in PMC_DOUBLE_BRACKET_NOLINK_RE.finditer(answer):
        ids.add(_normalize_pmcid(m.group(1)))
    # [PMC..., PMC...]
    for m in PMC_MULTI_BRACKET_RE.finditer(answer):
        group = m.group(1)
        for tok in group.split(","):
            ids.add(_normalize_pmcid(tok))
    # [PMC...]
    for m in PMC_SINGLE_BRACKET_RE.finditer(answer):
        ids.add(_normalize_pmcid(m.group(1)))
    ids.discard("")
    return ids

def _link_citations_md(answer: str, pmc_map: Dict[str, str]) -> str:
    """
    Convert citation markers in 'answer' into markdown hyperlinks using pmc_map.
    Handles:
      - [[PMC123]]  (no link) -> [[PMC123]](url)
      - [PMC123]    -> [[PMC123]](url)
      - [PMC123, PMC456] -> [[PMC123]](url), [[PMC456]](url)
    Leaves unknown PMCIDs as-is.
    """
    if not answer:
        return ""

    def linkify(pmc_raw: str) -> str:
        pmc = _normalize_pmcid(pmc_raw)
        url = pmc_map.get(pmc)
        return f"[[{pmc}]]({url})" if url else f"[{pmc_raw}]"

    # 1) Handle multi-citation bracket first to avoid conflicts
    def repl_multi(m: re.Match) -> str:
        group = m.group(1)
        toks = [t.strip() for t in group.split(",") if t.strip()]
        linked = []
        for t in toks:
            linked.append(linkify(t))
        return ", ".join(linked)

    out = PMC_MULTI_BRACKET_RE.sub(repl_multi, answer)

    # 2) Handle double bracket without link: [[PMC...]]  -> [[PMC...]](url)
    def repl_double_no_link(m: re.Match) -> str:
        pmc_raw = m.group(1)
        pmc = _normalize_pmcid(pmc_raw)
        url = pmc_map.get(pmc)
        return f"[[{pmc}]]({url})" if url else m.group(0)

    out = PMC_DOUBLE_BRACKET_NOLINK_RE.sub(repl_double_no_link, out)

    # 3) Handle single bracket: [PMC...] -> [[PMC...]](url)
    def repl_single(m: re.Match) -> str:
        pmc_raw = m.group(1)
        pmc = _normalize_pmcid(pmc_raw)
        url = pmc_map.get(pmc)
        return f"[[{pmc}]]({url})" if url else m.group(0)

    out = PMC_SINGLE_BRACKET_RE.sub(repl_single, out)

    return out

def _sanitize_caption(caption: str, max_chars: int) -> str:
    if not caption:
        return ""
    cleaned = re.sub(r"\s+", " ", caption).strip()
    if max_chars and max_chars > 0:
        return cleaned[:max_chars]
    return cleaned

def _render_figures_md(result: Dict[str, Any], fig_max_images: int = 2, fig_caption_max_chars: int = 0) -> str:
    figs = result.get("figures") or []
    if not figs:
        return ""
    pmc_map = _build_pmc_url_map(result.get("sources") or [])
    lines: List[str] = []
    lines.append("\n## Figures\n")
    for f in figs:
        pmcid_raw = f.get("pmcid", "")
        pmcid = _normalize_pmcid(str(pmcid_raw))
        label = (f.get("label") or "").strip()
        raw_caption = f.get("caption") or ""
        caption = _sanitize_caption(raw_caption, fig_caption_max_chars)
        tileshop = (f.get("tileshop") or "").strip() or None
        article_url = pmc_map.get(pmcid, f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/")
        title_label = f"{label}" if label else "Figure"

        head = f"-  __{title_label}__  \n"
        if caption:
            head += f"{caption}"
        lines.append(head)

        src_line = "  - __Source__"
        if pmcid:
            src_line += f" [[{pmcid}]]({article_url})"
        if tileshop:
            src_line += f" | [[Tileshop]]({tileshop})"
        lines.append(src_line)

        imgs = (f.get("images") or [])[:max(0, fig_max_images)]
        if imgs:
            lines.append("  - __Images__  ")
            for im in imgs:
                url = im.get("url")
                if not url:
                    continue
                alt = (label or pmcid)[:80]
                lines.append(f"    ![{alt}]({url})")
    return "\n".join(lines)

def _render_sources_md_cited_only(answer: str, sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return ""
    cited_ids = _extract_cited_pmcids(answer)
    if not cited_ids:
        return ""
    # build normalized index
    by_pmc: Dict[str, Dict[str, Any]] = {}
    for s in sources:
        pmc = _normalize_pmcid(s.get("pmcid", ""))
        if pmc:
            by_pmc[pmc] = s

    lines: List[str] = []
    lines.append("\n## Sources\n")
    for pmc in sorted(cited_ids):
        s = by_pmc.get(pmc, {})
        title = (s.get("title") or "").strip()
        url = s.get("url") or f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/"
        lines.append(f"-  {title or pmc}")
        lines.append(f"[[{pmc}]]({url})")
    return "\n".join(lines)

def _render_answer_md(question: str, answer: str, sources: List[Dict[str, Any]]) -> str:
    pmc_map = _build_pmc_url_map(sources)
    answer_linked = _link_citations_md(answer, pmc_map)

    parts: List[str] = []
    parts.append("# Answer\n")
    parts.append(f"> ### Question: {question}\n")
    parts.append(answer_linked.strip() + "\n")
    return "\n".join(parts)

# build_markdown: run_query 결과를 받아 Markdown 1개 문자열로 조립
def build_markdown(
    question: str,
    result: Dict[str, Any],
    *,
    include_sources: bool = True,
    include_figures: bool = True,
    fig_max_images: int = 2,
    fig_caption_max_chars: int = 0,
) -> str:
    """
    run_query -> Markdown return
    """
    parts = []

    answer_md = _render_answer_md(question, result.get("answer", ""), result.get("sources") or [])
    if answer_md and answer_md.strip():
        parts.append(answer_md)

    if include_sources:
        src_md = _render_sources_md_cited_only(result.get("answer", ""), result.get("sources") or [])
        if src_md and src_md.strip():
            parts.append(src_md)

    if include_figures:
        fig_md = _render_figures_md(
            result,
            fig_max_images=fig_max_images,
            fig_caption_max_chars=fig_caption_max_chars,
        )
        if fig_md and fig_md.strip():
            parts.append(fig_md)

    # Topic line (from result["topic"])
    topic = (result.get("topic") or "").strip()
    if topic:
        parts.append(f"\n> #### Topic : {topic}\n")

    return "\n".join(p for p in parts if p and p.strip())


def query_to_markdown(
    question: str,
    *,
    index_path: Optional[str] = INDEX_PATH,
    meta_path: Optional[str] = META_PATH,
    embed_model: Optional[str] = "text-embedding-3-small",
    chat_model: Optional[str] = "gpt-4o-mini",
    k_per_query: int = 6,
    top_k_final: int = 6,
    enable_reform: bool = True,
    use_hyde: bool = True,
    n_llm_rewrites: int = 3,
    include_sources: bool = True,
    include_figures: bool = True,
    fig_max_images: int = 2,
    fig_caption_max_chars: int = 0,
) -> str:
    """
    내부적으로 run_query를 실행하고, 그 결과를 Markdown 문자열로 반환합니다.
    외부 서비스/엔드포인트에서 바로 import하여 사용 가능합니다.
    """

    result = run_query(
        question=question,
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
    return build_markdown(
        question,
        result,
        include_sources=include_sources,
        include_figures=include_figures,
        fig_max_images=fig_max_images,
        fig_caption_max_chars=fig_caption_max_chars,
    )

# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("-q", "--question", required=True)
#     ap.add_argument("--index", default="data/index/faiss.index")
#     ap.add_argument("--meta", default="data/index/meta.jsonl")
#     ap.add_argument("--articles", default="articles")
#     ap.add_argument("--embed-model", default=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"))
#     ap.add_argument("--chat-model", default=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"))
#     ap.add_argument("--k-per-query", type=int, default=6)
#     ap.add_argument("--top-k", type=int, default=6)
#     ap.add_argument("--no-reform", action="store_true")
#     ap.add_argument("--no-hyde", action="store_true")
#     ap.add_argument("--n-llm", type=int, default=6)
#     ap.add_argument("--json", action="store_true", help="print JSON result")
#     ap.add_argument("--fig-max-images", type=int, default=2, help="max images to render per figure (default 2)")
#     ap.add_argument("--fig-caption-max-chars", type=int, default=0, help="max characters for figure captions (0 = unlimited)")
#     args = ap.parse_args()

#     result = run_query(
#         question=args.question,
#         index_path=Path(args.index),
#         meta_path=Path(args.meta),
#         embed_model=args.embed_model,
#         chat_model=args.chat_model,
#         k_per_query=args.k_per_query,
#         top_k_final=args.top_k,
#         enable_reform=(not args.no_reform),
#         use_hyde=(not args.no_hyde),
#         n_llm_rewrites=args.n_llm,
#     )

#     if args.json:
#         print(json.dumps(result, ensure_ascii=False, indent=2))
#         return

#     md_parts: List[str] = []
#     md_parts.append(_render_answer_md(args.question, result.get("answer", ""), result.get("sources") or []))
#     md_parts.append(_render_sources_md_cited_only(result.get("answer", ""), result.get("sources") or []))
#     md_parts.append(_render_figures_md(
#         result,
#         fig_max_images=args.fig_max_images,
#         fig_caption_max_chars=args.fig_caption_max_chars
#     ))

#     print("\n".join([p for p in md_parts if p.strip()]))

# if __name__ == "__main__":
#     main()