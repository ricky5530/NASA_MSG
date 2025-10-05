#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure utilities
- Load figure metadata from meta.jsonl (built alongside FAISS index)
- Build figure index by label tokens (e.g., '1', '2A', 'S1', '2-1')
- Resolve "Figure N" / "Fig. N" references in text to tileshop/image URLs
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from functools import lru_cache
import json
import re

# Accepts: "Figure 1", "Fig. 2A", "Figure S1", "Figure 2-1"
FIG_NUM_RE = re.compile(r'\b(?:Fig(?:ure)?\.?)\s+([0-9A-Za-z\-\u2013\u2014\.]+)', re.I)

# Compute absolute meta.jsonl path relative to this script
BASE_DIR = Path(__file__).resolve().parents[1]
META_PATH = BASE_DIR / "data" / "index" / "meta.jsonl"

@lru_cache(maxsize=1)
def _load_meta_fig_index(meta_path_str: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan meta.jsonl once and cache a mapping: pmcid -> [figure_objs].
    Each figure_obj contains {id, label, caption, tileshop, images[]}.
    """
    meta_path = Path(meta_path_str)
    out: Dict[str, List[Dict[str, Any]]] = {}
    if not meta_path.exists():
        return out
    try:
        with meta_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if (obj.get("type") or "").lower() != "figure":
                    continue
                pmcid = obj.get("pmcid")
                if not pmcid:
                    continue

                label = obj.get("figure_label") or ""
                caption = obj.get("figure_caption")
                tileshop = obj.get("figure_tileshop")
                img_urls = obj.get("figure_image_urls") or []
                images = [{"url": u, "filename": Path(u).name} for u in img_urls]

                fig_obj = {
                    "id": obj.get("id"),
                    "label": label,
                    "caption": caption,
                    "tileshop": tileshop,
                    "images": images,
                }
                out.setdefault(pmcid, []).append(fig_obj)
    except Exception:
        return {}
    return out

def load_article_json(pmcid: str) -> Dict[str, Any]:
    # Compatibility shim: return a minimal article-like object with figures only,
    # sourced from meta.jsonl rather than per-article article.json.
    figs = _load_meta_fig_index(str(META_PATH)).get(pmcid) or []
    return {"figures": figs} if figs else {}

def _norm_token(tok: str) -> str:
    t = (tok or "").strip()
    # normalize dashes and case
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("–", "-").replace("—", "-")
    return t.upper()

def build_figure_index(article_obj: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Return mapping:
      key -> figure_obj
    where key examples: '1', '2', '2A', 'S1', '2-1'
    """
    idx: Dict[str, Dict[str, Any]] = {}
    figs = (article_obj.get("figures") or [])
    for fig in figs:
        label = (fig.get("label") or "").strip()
        if not label:
            continue
        # Try to parse "Figure <token>" within the label
        m = FIG_NUM_RE.search(label)
        if not m:
            # Fallback: keep entire label as a key too
            idx[_norm_token(label)] = fig
            continue
        token = _norm_token(m.group(1))
        idx[token] = fig
        # Also add a couple of relaxed variants:
        # '2A' -> '2-A', '2-A' -> '2A'
        if '-' in token:
            idx[token.replace('-', '')] = fig
        else:
            # add dashed version between number-letter (e.g., 2A -> 2-A)
            m2 = re.match(r'^(\d+)([A-Z]+)$', token)
            if m2:
                idx[f"{m2.group(1)}-{m2.group(2)}"] = fig
    return idx

def find_figure_refs(text: str) -> List[str]:
    """
    Extract raw tokens referenced in text, normalized.
    """
    out: List[str] = []
    for m in FIG_NUM_RE.finditer(text or ""):
        out.append(_norm_token(m.group(1)))
    return out

def resolve_figures_from_text(
    text: str,
    article_obj: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Given a chunk text and the source article, return the figures referenced in the text.
    """
    refs = find_figure_refs(text)
    if not refs:
        return []
    idx = build_figure_index(article_obj)
    seen: Set[str] = set()
    out: List[Dict[str, Any]] = []
    for tok in refs:
        cand: Optional[Dict[str, Any]] = idx.get(tok)
        if not cand:
            # try a couple of relaxed variants
            t2 = tok.replace('-', '')
            cand = idx.get(t2)
        if not cand:
            continue
        key = cand.get("id") or cand.get("label") or tok
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "id": cand.get("id"),
            "label": cand.get("label"),
            "caption": cand.get("caption"),
            "tileshop": cand.get("tileshop"),
            "images": [{"url": im.get("url"), "filename": im.get("filename")} for im in (cand.get("images") or [])],
        })
    return out

def collect_figures_for_docs(
    docs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Inspect retrieved docs and collect figure attachments.
    - If doc type == 'figure': use its own metadata
    - Else: scan text for "Figure N" references and resolve via article.json
    Return: list of {pmcid, label, caption, tileshop, images}
    """
    figures: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for d in docs:
        meta = d.get("metadata") or {}
        pmcid = meta.get("pmcid")
        if not pmcid:
            continue

        # Case 1: figure chunk directly
        if (meta.get("type") or "").lower() == "figure":
            label = meta.get("figure_label")
            key = f"{pmcid}::{label}"
            if key in seen:
                continue
            seen.add(key)
            figures.append({
                "pmcid": pmcid,
                "label": label,
                "caption": meta.get("figure_caption"),
                "tileshop": meta.get("figure_tileshop"),
                "images": [{"url": u, "filename": Path(u).name} for u in (meta.get("figure_image_urls") or [])],
            })
            continue

        # Case 2: resolve "Figure N" in text
        article_obj = load_article_json(pmcid)
        if not article_obj:
            continue
        resolved = resolve_figures_from_text(d.get("page_content") or "", article_obj)
        for fig in resolved:
            key = f"{pmcid}::{fig.get('label') or fig.get('id')}"
            if key in seen:
                continue
            seen.add(key)
            figures.append({
                "pmcid": pmcid,
                **fig,
            })
    return figures