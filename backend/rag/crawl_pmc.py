#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC HTML 전용 크롤러/파서 + CSV 배치 실행
- 이미지는 다운로드하지 않고 URL만 저장
- 단일 입력: PMC HTML URL 또는 로컬 html 파일 경로
- CSV 배치: data/raw/SB_publication_PMC.csv (기본 헤더: Title,Link)

출력:
  - {out_dir}/{PMCID}/article.md
  - {out_dir}/{PMCID}/article.json (이미지 URL 포함)

예시:
  # CSV 상위 10개만, 이미 처리된 항목은 건너뛰기
  python scripts/crawl_pmc.py --csv data/raw/SB_publication_PMC.csv --limit 10 --resume --out articles

  # 단일 URL
  python scripts/crawl_pmc.py "https://pmc.ncbi.nlm.nih.gov/articles/PMC2824534/" --out articles

필수 패키지:
  pip install -U beautifulsoup4 lxml requests
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Iterable
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
REQ_TIMEOUT = 20

FIG_NUM_RE = re.compile(r"Figure\s+([0-9A-Za-z\-\u2013\u2014\.]+)")
PMCID_RE = re.compile(r"/articles/(PMC\d+)/", re.I)

@dataclass
class FigureImage:
    url: str          # 이미지 URL (다운로드 안 함)
    filename: str     # 추론된 파일명

@dataclass
class Figure:
    id: str
    label: str
    caption: str
    images: List[FigureImage]
    tileshop: Optional[str] = None

@dataclass
class Section:
    level: int
    title: str
    markdown: str

@dataclass
class ArticleData:
    title: str
    pmcid: Optional[str]
    doi: Optional[str]
    pmid: Optional[str]
    pdf_url: Optional[str]
    canonical: Optional[str]
    journal: Optional[str]
    published: Optional[str]
    sections: List[Section]
    figures: List[Figure]

def fetch_html(input_path_or_url: str) -> Tuple[str, str]:
    """Return (html_text, source_url_or_path)"""
    if input_path_or_url.startswith("http://") or input_path_or_url.startswith("https://"):
        session = requests.Session()
        session.headers.update({"User-Agent": UA, "Accept": "text/html, */*"})
        last_exc = None
        for _ in range(3):
            try:
                r = session.get(input_path_or_url, timeout=REQ_TIMEOUT)
                r.raise_for_status()
                r.encoding = r.apparent_encoding or r.encoding or "utf-8"
                return r.text, input_path_or_url
            except Exception as e:
                last_exc = e
                time.sleep(1.2)
        raise RuntimeError(f"Failed to fetch URL: {input_path_or_url} ({last_exc})")
    else:
        p = Path(input_path_or_url)
        if not p.exists():
            raise FileNotFoundError(p)
        return p.read_text(encoding="utf-8", errors="ignore"), str(p.resolve())

def text_of(el: Optional[Tag]) -> str:
    if not el:
        return ""
    for s in el.select("script, style"):
        s.decompose()
    return " ".join(el.get_text(" ", strip=True).split())

def ext_from_url(u: str) -> str:
    path = urlparse(u).path
    ext = os.path.splitext(path)[1].lower()
    if ext:
        return ext
    return ".jpg"

def infer_pmcid(soup: BeautifulSoup) -> Optional[str]:
    # 1) canonical link
    link = soup.find("link", rel="canonical")
    if link and link.get("href"):
        m = PMCID_RE.search(link["href"])
        if m:
            return m.group(1)
    # 2) data-article-id 속성
    cont = soup.find(attrs={"data-article-id": True})
    if cont:
        return f"PMC{cont['data-article-id']}"
    return None

def extract_meta(soup: BeautifulSoup) -> dict:
    meta = {}
    def m(name):
        return soup.find("meta", attrs={"name": name})
    meta["title"] = (m("citation_title") or {}).get("content") if m("citation_title") else None
    meta["journal"] = (m("citation_journal_title") or {}).get("content") if m("citation_journal_title") else None
    meta["doi"] = (m("citation_doi") or {}).get("content") if m("citation_doi") else None
    meta["pmid"] = (m("citation_pmid") or {}).get("content") if m("citation_pmid") else None
    meta["pdf_url"] = (m("citation_pdf_url") or {}).get("content") if m("citation_pdf_url") else None
    meta["published"] = (m("citation_publication_date") or {}).get("content") if m("citation_publication_date") else None
    link = soup.find("link", rel="canonical")
    meta["canonical"] = link["href"] if link and link.get("href") else None
    if not meta["title"]:
        h1 = soup.select_one(".front-matter h1") or soup.find("h1")
        meta["title"] = text_of(h1) if h1 else text_of(soup.find("title"))
    meta["pmcid"] = infer_pmcid(soup)
    return meta

def to_markdown_from_nodes(nodes: List[Tag], include_headings: bool = False) -> str:
    """
    아주 단순한 HTML → MD 변환.
    - 기본값으로 섹션 헤더(h1~h6)는 제외(include_headings=False).
      (헤더 출력은 render_markdown()에서 일괄 처리)
    """
    out: List[str] = []
    for node in nodes:
        if isinstance(node, NavigableString):
            txt = str(node).strip()
            if txt:
                out.append(txt)
            continue
        if not isinstance(node, Tag):
            continue
        # skip figures/tables/aside
        if node.name in ("figure", "table", "aside"):
            continue
        if node.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if include_headings:
                level = {"h1":"#","h2":"##","h3":"###","h4":"####","h5":"#####","h6":"######"}[node.name]
                out.append(f"{level} {text_of(node)}")
            continue
        if node.name == "p":
            t = text_of(node)
            if t:
                out.append(t)
            continue
        if node.name in ("ul", "ol"):
            is_ol = node.name == "ol"
            for i, li in enumerate(node.find_all("li", recursive=False), 1):
                bullet = f"{i}." if is_ol else "-"
                out.append(f"{bullet} {text_of(li)}")
            continue
        t = text_of(node)
        if t:
            out.append(t)
    return "\n\n".join([s for s in out if s])

def extract_sections(soup: BeautifulSoup) -> List[Section]:
    main = soup.select_one("section.body.main-article-body")
    if not main:
        return []
    sections: List[Section] = []

    # Abstract
    abs_sec = main.select_one("section.abstract")
    if abs_sec:
        nodes = [c for c in abs_sec.find_all(recursive=False)]
        md = to_markdown_from_nodes(nodes, include_headings=False)
        if md.strip():
            sections.append(Section(level=2, title="Abstract", markdown=md))

    # Top-level sections (excluding abstract)
    for sec in main.find_all("section", recursive=False):
        if "abstract" in sec.get("class", []):
            continue
        h = sec.find(["h2", "h3"])
        title = text_of(h) if h else ""
        level = 2 if (h and h.name == "h2") else 3
        nodes = [c for c in sec.children if isinstance(c, (Tag, NavigableString))]
        md = to_markdown_from_nodes(nodes, include_headings=False)
        if title or md.strip():
            sections.append(Section(level=level, title=title, markdown=md))
    return sections

def extract_figures(soup: BeautifulSoup, base_url: str) -> List[Figure]:
    """이미지는 다운로드하지 않고 URL만 저장"""
    figures: List[Figure] = []
    for fig in soup.select("section.body.main-article-body figure.fig"):
        fig_id = fig.get("id") or ""
        label = text_of(fig.find("h4", class_="obj_head"))
        caption = text_of(fig.find("figcaption"))
        tile = fig.select_one("a.tileshop")
        tileshop_url = tile.get("href") if tile and tile.get("href") else None

        imgs: List[FigureImage] = []
        for k, img in enumerate(fig.select("img.graphic"), 1):
            src = img.get("src")
            if not src:
                continue
            
            # 상대 URL을 절대 URL로 변환
            full_url = urljoin(base_url, src)
            
            # Figure 번호 추출
            fig_num = "X"
            m = FIG_NUM_RE.search(label or "")
            if m:
                fig_num = str(m.group(1)).replace(".", "")
            base_name = f"F{fig_num}"
            if k > 1:
                base_name = f"{base_name}_{k}"
            ext = ext_from_url(src)
            filename = f"{base_name}{ext}"
            
            imgs.append(FigureImage(url=full_url, filename=filename))

        figures.append(Figure(id=fig_id, label=label, caption=caption, images=imgs, tileshop=tileshop_url))
    
    return figures

def render_markdown(article: ArticleData) -> str:
    """이미지는 URL로만 표시"""
    lines: List[str] = []
    lines.append(f"# {article.title}")
    meta_line = []
    if article.journal: meta_line.append(article.journal)
    if article.published: meta_line.append(article.published)
    if article.doi: meta_line.append(f"DOI: {article.doi}")
    if article.pmid: meta_line.append(f"PMID: {article.pmid}")
    if article.pmcid: meta_line.append(f"PMCID: {article.pmcid}")
    if meta_line:
        lines.append("")
        lines.append("- " + " | ".join(meta_line))
    if article.pdf_url:
        lines.append(f"- PDF: {article.pdf_url}")
    if article.canonical:
        lines.append(f"- Canonical: {article.canonical}")

    for s in article.sections:
        if s.title:
            lines.append("")
            if s.level == 2:
                lines.append(f"## {s.title}")
            else:
                lines.append(f"### {s.title}")
        if s.markdown.strip():
            lines.append("")
            lines.append(s.markdown.strip())

    if article.figures:
        lines.append("")
        lines.append("## Figures")
        for fig in article.figures:
            lines.append("")
            title = fig.label or fig.id or "Figure"
            lines.append(f"### {title}")
            if fig.caption:
                lines.append("")
                lines.append(fig.caption)
            for img in fig.images:
                lines.append("")
                lines.append(f"![{title}]({img.url})")  # URL 직접 사용
            if fig.tileshop:
                lines.append("")
                lines.append(f"- Tileshop: {fig.tileshop}")

    return "\n".join(lines).strip() + "\n"

def crawl_one(input_path_or_url: str, out_root: Path) -> Tuple[bool, Optional[str], str]:
    """
    단일 URL/로컬 HTML을 크롤링하여 out_root/PMCID/* 로 저장
    Returns: (success, pmcid, message)
    """
    try:
        html, source_url = fetch_html(input_path_or_url)
        soup = BeautifulSoup(html, "lxml")

        meta = extract_meta(soup)
        pmcid = meta.get("pmcid") or "PMC_UNKNOWN"
        target_root = out_root / pmcid

        sections = extract_sections(soup)
        figures = extract_figures(soup, source_url)  # base_url 전달

        article = ArticleData(
            title=meta.get("title") or "Untitled",
            pmcid=pmcid if pmcid != "PMC_UNKNOWN" else None,
            doi=meta.get("doi"),
            pmid=meta.get("pmid"),
            pdf_url=meta.get("pdf_url"),
            canonical=meta.get("canonical"),
            journal=meta.get("journal"),
            published=meta.get("published"),
            sections=sections,
            figures=figures,
        )

        target_root.mkdir(parents=True, exist_ok=True)
        md = render_markdown(article)
        (target_root / "article.md").write_text(md, encoding="utf-8")

        # JSON 저장 (이미지 URL 포함)
        json_obj = asdict(article)
        json_obj["sections"] = [asdict(s) for s in article.sections]
        json_obj["figures"] = [
            {
                "id": f.id,
                "label": f.label,
                "caption": f.caption,
                "tileshop": f.tileshop,
                "images": [{"url": i.url, "filename": i.filename} for i in f.images],
            }
            for f in article.figures
        ]
        (target_root / "article.json").write_text(json.dumps(json_obj, ensure_ascii=False, indent=2), encoding="utf-8")

        return True, pmcid, f"Saved to: {target_root.resolve()}"
    except Exception as e:
        return False, None, f"error: {e}"

def iter_csv_links(csv_path: Path, limit: int = 0) -> Iterable[str]:
    """
    CSV 헤더: Title,Link
    limit > 0 이면 상단부터 limit개 반환
    """
    count = 0
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = (row.get("Link") or "").strip()
            if not link:
                continue
            yield link
            count += 1
            if limit and count >= limit:
                break

def pmcid_from_url(url: str) -> Optional[str]:
    m = PMCID_RE.search(url)
    return m.group(1) if m else None

def main():
    ap = argparse.ArgumentParser(description="PMC HTML-only crawler/parser (images as URLs only)")
    ap.add_argument("input", nargs="?", help="Single PMC HTML URL or local html file path (omit if using --csv)")
    ap.add_argument("--csv", default=None, help="CSV path with headers Title,Link (e.g., data/raw/SB_publication_PMC.csv)")
    ap.add_argument("--limit", type=int, default=0, help="Process only first N rows from CSV (0 = all)")
    ap.add_argument("--out", default="articles", help="Output root directory (default: articles)")
    ap.add_argument("--resume", action="store_true", help="Skip if {out}/PMCID/article.json already exists")
    args = ap.parse_args()

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    # CSV 배치 모드
    if args.csv:
        csv_path = Path(args.csv).resolve()
        if not csv_path.exists():
            print(f"[error] CSV not found: {csv_path}", file=sys.stderr)
            sys.exit(2)

        total = 0
        ok = 0
        start = time.time()
        for idx, url in enumerate(iter_csv_links(csv_path, limit=args.limit), 1):
            # resume 스킵 판단(가능하면 URL에서 PMCID 추정)
            if args.resume:
                pmcid_guess = pmcid_from_url(url)
                if pmcid_guess:
                    if (out_root / pmcid_guess / "article.json").exists():
                        print(f"[skip] ({idx}) {pmcid_guess} already exists for {url}")
                        total += 1
                        continue
            print(f"[run] ({idx}) {url}")
            success, pmcid, msg = crawl_one(url, out_root)
            status = "ok" if success else "fail"
            if success:
                ok += 1
            total += 1
            tag = pmcid or "-"
            print(f"[{status}] {tag} - {msg}")
        dur = time.time() - start
        print(f"[done] total={total} ok={ok} fail={total-ok} elapsed={dur:.1f}s out={out_root}")
        sys.exit(0)

    # 단일 실행 모드
    if not args.input:
        print("[error] Provide either a single input or --csv path", file=sys.stderr)
        sys.exit(2)

    success, pmcid, msg = crawl_one(args.input, out_root)
    print(("[ok]" if success else "[fail]"), pmcid or "-", "-", msg)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()