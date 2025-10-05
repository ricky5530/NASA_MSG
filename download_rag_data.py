#!/usr/bin/env python3
"""
Download FAISS index from external storage on first run
"""
import os
from pathlib import Path
import requests
import logging

logger = logging.getLogger(__name__)

FAISS_INDEX_URL = os.getenv("FAISS_INDEX_URL", "")
META_JSONL_URL = os.getenv("META_JSONL_URL", "")

def download_file(url: str, dest_path: Path):
    """Download file from URL to destination"""
    if not url:
        return False
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {dest_path.name}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info(f"✅ Downloaded {dest_path.name}")
    return True

def init_rag_data():
    """Initialize RAG data if not present"""
    backend_dir = Path(__file__).parent / "backend"
    index_path = backend_dir / "data" / "index" / "faiss.index"
    meta_path = backend_dir / "data" / "index" / "meta.jsonl"
    
    if index_path.exists() and meta_path.exists():
        logger.info("✅ FAISS index already exists")
        return True
    
    logger.warning("⚠️ FAISS index not found, attempting download...")
    
    try:
        if FAISS_INDEX_URL and META_JSONL_URL:
            download_file(FAISS_INDEX_URL, index_path)
            download_file(META_JSONL_URL, meta_path)
            return True
        else:
            logger.warning("⚠️ FAISS_INDEX_URL or META_JSONL_URL not set")
            logger.warning("⚠️ Will use MockRAGService")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to download FAISS data: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_rag_data()
