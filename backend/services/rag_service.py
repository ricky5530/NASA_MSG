#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NASA RAG Service for FastAPI backend
Uses query_pipeline.py from rag directory for actual RAG search
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add backend/rag to Python path
rag_dir = Path(__file__).parent.parent / "rag"
sys.path.insert(0, str(rag_dir))

try:
    from query_pipeline import run_query
    RAG_AVAILABLE = True
except ImportError as e:
    logging.warning(f"RAG modules not available: {e}")
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)


class NASARAGService:
    """
    Real NASA RAG service using query_pipeline.py
    """
    def __init__(
        self,
        index_path: Optional[Path] = None,
        meta_path: Optional[Path] = None,
        articles_dir: Optional[Path] = None,
        embed_model: Optional[str] = None,
        chat_model: Optional[str] = None,
    ):
        if not RAG_AVAILABLE:
            raise RuntimeError("RAG modules not available. Install required packages.")
        
        # Default paths relative to backend directory
        backend_dir = Path(__file__).parent.parent
        self.index_path = index_path or backend_dir / "data" / "index" / "faiss.index"
        self.meta_path = meta_path or backend_dir / "data" / "index" / "meta.jsonl"
        # articles_dir currently unused by query_pipeline.run_query (kept for future compatibility)
        self.articles_dir = articles_dir or (backend_dir / "articles")
        
        # Models
        self.embed_model = embed_model or os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self.chat_model = chat_model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        
        def _is_lfs_pointer(p: Path) -> bool:
            try:
                if not p.exists():
                    return False
                size = p.stat().st_size
                if size > 1024:  # >1KB이면 포인터일 가능성 낮음
                    return False
                with p.open('r', encoding='utf-8', errors='ignore') as f:
                    first = f.readline().strip()
                return first.startswith('version https://git-lfs.github.com/spec')
            except Exception:
                return False

        problems: list[str] = []

        # Index 파일 검증
        if not self.index_path.exists():
            problems.append(f"FAISS index not found: {self.index_path}")
        elif _is_lfs_pointer(self.index_path):
            problems.append(f"FAISS index is still an LFS pointer (git lfs pull needed): {self.index_path}")
        else:
            try:
                size_mb = self.index_path.stat().st_size / 1024 / 1024
                logger.info(f"✅ FAISS index present ({size_mb:.2f} MB)")
                if size_mb < 10:  # 비정상적으로 작은 경우
                    problems.append(f"FAISS index file size suspiciously small ({size_mb:.2f} MB)")
            except Exception as e:
                problems.append(f"Failed to stat index file: {e}")

        # Meta 파일 검증
        if not self.meta_path.exists():
            problems.append(f"meta.jsonl not found: {self.meta_path}")
        elif _is_lfs_pointer(self.meta_path):
            problems.append(f"meta.jsonl is still an LFS pointer (git lfs pull needed): {self.meta_path}")
        else:
            try:
                meta_size_mb = self.meta_path.stat().st_size / 1024 / 1024
                logger.info(f"✅ meta.jsonl present ({meta_size_mb:.2f} MB)")
                if meta_size_mb < 1:
                    problems.append(f"meta.jsonl size suspiciously small ({meta_size_mb:.2f} MB)")
            except Exception as e:
                problems.append(f"Failed to stat meta.jsonl: {e}")

        if problems:
            for p in problems:
                logger.warning(f"⚠️ {p}")
            logger.warning("⚠️ RAG service disabled due to missing / pointer files")
            self.available = False
        else:
            self.available = True
            logger.info("✅ RAG service file validation passed")
    
    def search(self, query: str) -> str:
        """
        Search NASA papers using run_query from query_pipeline
        
        Args:
            query: User's question
            
        Returns:
            RAG answer with citations
        """
        if not self.available:
            logger.warning("FAISS index not available, returning empty")
            return ""
        
        try:
            # Use run_query from query_pipeline.py
            result = run_query(
                question=query,
                index_path=self.index_path,
                meta_path=self.meta_path,
                embed_model=self.embed_model,
                chat_model=self.chat_model,
                k_per_query=6,
                top_k_final=6,
                enable_reform=True,
                use_hyde=True,
                n_llm_rewrites=3,
            )
            
            # result is a dict with: question, answer, sources, figures
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            logger.info(f"✅ RAG search found {len(sources)} sources")
            return answer
            
        except Exception as e:
            logger.error(f"❌ RAG search failed: {e}", exc_info=True)
            return ""
    
    def get_detailed_response(self, query: str) -> Dict[str, Any]:
        """
        Get full RAG response with answer, sources, and figures
        
        Args:
            query: User's question
            
        Returns:
            Dict with question, answer, sources, and figures
        """
        if not self.available:
            return {
                "question": query,
                "answer": "",  # 빈 답변으로 ChatService가 일반 모드로 처리하게 함
                "sources": [],
                "figures": []
            }
        
        try:
            result = run_query(
                question=query,
                index_path=self.index_path,
                meta_path=self.meta_path,
                embed_model=self.embed_model,
                chat_model=self.chat_model,
                k_per_query=6,
                top_k_final=6,
                enable_reform=True,
                use_hyde=True,
                n_llm_rewrites=3,
            )
            return result
        except Exception as e:
            logger.error(f"❌ RAG detailed response failed: {e}", exc_info=True)
            return {
                "question": query,
                "answer": f"An error occurred while processing your question: {str(e)}",
                "sources": [],
                "figures": []
            }


class MockRAGService:
    """
    Fallback mock RAG service when real RAG is not available
    """
    def search(self, query: str) -> str:
        """Return empty context for mock"""
        return ""
    
    def get_detailed_response(self, query: str) -> Dict[str, Any]:
        """Return empty response for mock - let ChatService handle with normal OpenAI"""
        return {
            "question": query,
            "answer": "",  # 빈 답변으로 ChatService가 일반 모드로 처리하게 함
            "sources": [],
            "figures": []
        }


def create_rag_service() -> NASARAGService | MockRAGService:
    """
    Factory function to create appropriate RAG service
    """
    if not RAG_AVAILABLE:
        logger.warning("⚠️ Using MockRAGService (RAG modules not available)")
        return MockRAGService()
    
    try:
        service = NASARAGService()
        if not service.available:
            logger.warning("⚠️ Using MockRAGService (FAISS index not found)")
            return MockRAGService()
        return service
    except Exception as e:
        logger.error(f"❌ Failed to create NASARAGService: {e}")
        logger.warning("⚠️ Falling back to MockRAGService")
        return MockRAGService()
