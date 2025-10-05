import logging
import os
import re
import schedule
import sys
import threading
import time

from collections import deque, Counter
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Body, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# .env 파일 로드 (현재 디렉토리에서)
load_dotenv('.env')  # backend/.env 파일 로드

# 서비스 임포트 - 절대 임포트로 변경 (Render 배포 호환)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 데이터베이스 임포트
from database import cleanup_old_data, get_database_size, vacuum_database

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent        # backend/
ROOT_DIR = BASE_DIR.parent  

INDEX_PATH = BASE_DIR / "data" / "index" / "faiss.index"
META_PATH = BASE_DIR / "data" / "index" / "meta.jsonl"

# 데이터베이스 정리 스케줄러
def run_database_cleanup():
    """데이터베이스 정리 작업 실행"""
    try:
        logger.info("📊 데이터베이스 정리 시작...")
        
        # 현재 크기 확인
        current_size = get_database_size()
        logger.info(f"정리 전 데이터베이스 크기: {current_size}MB")
        
        # 24시간 이상 된 데이터 정리
        result = cleanup_old_data(hours_to_keep=24)
        
        # VACUUM으로 공간 재확보
        vacuum_database()
        
        # 정리 후 크기 확인
        new_size = get_database_size()
        saved_space = current_size - new_size
        
        logger.info(f"정리 완료! 크기: {new_size}MB (절약: {saved_space:.2f}MB)")
        logger.info(f"삭제된 항목: 메시지 {result['deleted_messages']}개, 대화 {result['deleted_conversations']}개, 사용자 {result['deleted_users']}개")
        
    except Exception as e:
        logger.error(f"데이터베이스 정리 중 오류: {e}")

def setup_scheduler():
    """스케줄러 설정 및 시작"""
    # 매일 오전 3시에 정리 실행
    schedule.every().day.at("03:00").do(run_database_cleanup)
    
    # 12시간마다 정리 (더 자주)
    schedule.every(12).hours.do(run_database_cleanup)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    
    # 백그라운드 스레드에서 스케줄러 실행
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("⏰ 데이터베이스 정리 스케줄러 시작됨 (12시간마다)")

@asynccontextmanager
async def lifespan(app):
    logger.info("🌟 Lifespan 시작!")
    
    # 초기 데이터베이스 크기 확인
    initial_size = get_database_size()
    logger.info(f"현재 데이터베이스 크기: {initial_size}MB")
    
    # 스케줄러 시작
    setup_scheduler()
    
    # 시작 시 한 번 정리 (크기가 10MB 이상인 경우)
    if initial_size > 10:
        logger.info("큰 데이터베이스 감지, 초기 정리 실행...")
        run_database_cleanup()

    try:
        yield
    finally:
        logger.info("🛑 Lifespan 종료!")

# Heuristic으로 언어 감지 -> Dashboard에 update
def detect_language_heuristic(text: str) -> str:
    if not text:
        return "unknown"
    if re.search(r"[가-힣]", text):
        return "korean"
    if re.search(r"[\u3040-\u30FF]", text):
        return "japanese"
    if re.search(r"[\u4E00-\u9FFF]", text):
        return "chinese"
    if any(c in text for c in "ñáéíóúü¿¡"):
        return "spanish"
    if re.search(r"[\u0400-\u04FF]", text):
        return "russian"
    if re.search(r"[\u0600-\u06FF]", text):
        return "arabic"
    return "english"

# =========================
# In-memory Dashboard State
# =========================
DASHBOARD = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "messages_total": 0,
    "events": deque(maxlen=1000),      # [(ts_epoch, lang, topic, preview)]
    "latencies_ms": deque(maxlen=500), # recent latencies
    "lang_counter": Counter(),         # language distribution
    "topic_counter": Counter(),        # topic distribution
    "recent": deque(maxlen=50),        # recent activity list
}

# FastAPI 앱 초기화 (lifespan 훅 포함)
app = FastAPI(lifespan=lifespan)

# 앱 메타데이터 추가
app.title = "MARS - Mission for Astrobiology and Research Support"
app.description = "NASA Space Apps Challenge - MSG"
app.version = "1.0.0"

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://nasamsg.vercel.app",
        "https://*.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# CORS preflight 처리를 위한 미들웨어
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response()
        response.headers["access-control-allow-origin"] = "*"
        response.headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["access-control-allow-headers"] = "*"
        response.headers["access-control-allow-credentials"] = "true"
        return response
    
    response = await call_next(request)
    response.headers["access-control-allow-origin"] = "*"
    response.headers["access-control-allow-credentials"] = "true"
    return response

@app.get("/")
@app.head("/")
async def root():
    """서버 상태 확인"""
    return {
        "message": "🚀 NASA Space Biology Chatbot API - 실제 논문 학습 시스템",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "607개 NASA 우주생물학 논문 학습",
            "RAG 기반 정확한 답변",
            "실시간 논문 검색"
        ]
    }

# 사용자 세션 시작 API (데이터베이스 의존성 제거)
@app.post("/user/session/start")
async def start_user_session(request: Request):
    """사용자 세션 시작 - 세션 ID 생성"""
    try:
        # 세션 ID 생성 (브라우저 식별용)
        session_id = request.headers.get("x-session-id") or f"session_{int(time.time() * 1000)}"
        
        # 단순 사용자 ID 생성 (데이터베이스 없이)
        user_id = f"user_{session_id}"
        
        logger.info(f"👤 User session started: {user_id} (session: {session_id})")
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "status": "session_started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Session start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/rag/md")
async def rag_markdown(payload: dict = Body(...)):
    """
    질문을 받아 Markdown으로 구성된 답변을 반환 (Content-Type: text/markdown)
    request body 예:
    {
      "question": "질문",
      "include_sources": true,
      "include_figures": true,
      "fig_max_images": 2,
      "fig_caption_max_chars": 0
    }
    """
    # 안전한 import (패키지/네임스페이스 환경 모두 지원)
    try:
        from backend.rag.query_markdown import query_to_markdown
    except Exception:
        import sys as _sys
        _sys.path.append(str(BASE_DIR / "rag"))
        from query_markdown import query_to_markdown  # type: ignore

    q = (payload.get("question") or payload.get("message") or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="question (or message) is required")

    include_sources = bool(payload.get("include_sources", True))
    include_figures = bool(payload.get("include_figures", True))
    fig_max_images = int(payload.get("fig_max_images", 2))
    fig_caption_max_chars = int(payload.get("fig_caption_max_chars", 0))

    try:
        start_ts = time.time()
        index_path = INDEX_PATH
        meta_path = META_PATH

        md = query_to_markdown(
            q,
            index_path=index_path,
            meta_path=meta_path,
            # 모델/파라미터는 필요 시 환경변수로 주입 가능
            include_sources=include_sources,
            include_figures=include_figures,
            fig_max_images=fig_max_images,
            fig_caption_max_chars=fig_caption_max_chars,
        )
        # 대시보드 업데이트
        try:
            latency_ms = (time.time() - start_ts) * 1000.0
            lang = detect_language_heuristic(q)

            topic = None
            try:
                for line in reversed(md.splitlines()):
                    s = line.strip()
                    if s.lower().startswith("> #### topic :".lower()):
                        topic = s.split(":", 1)[1].strip()
                        break
            except Exception:
                topic = None
            # 토픽이 없으면 집계 생략 (표시/카운트 모두 건너뜀)
            has_topic = bool(topic)

            preview = q.replace("\n", " ").strip()
            if len(preview) > 80:
                preview = preview[:77] + "..."

            DASHBOARD["messages_total"] += 1
            DASHBOARD["latencies_ms"].append(latency_ms)
            DASHBOARD["lang_counter"][lang] += 1
            ts = time.time()
            if has_topic:
                DASHBOARD["topic_counter"][topic] += 1
                DASHBOARD["events"].append((ts, lang, topic, preview))
            else:
                DASHBOARD["events"].append((ts, lang, "", preview))
            DASHBOARD["recent"].appendleft({
                "ts": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "language": lang,
                "topic": topic,
                "text": preview,
            })
        except Exception as _:
            # 대시보드 집계는 실패해도 본문 응답에는 영향 주지 않음
            pass
    except Exception as e:
        logger.error(f"❌ RAG markdown response failed: {e}", exc_info=True)
        md = f"# Error\n\n질문 처리 중 오류가 발생했습니다.\n\n```\n{str(e)}\n```"

    return Response(content=md, media_type="text/markdown")

@app.get("/dashboard/summary")
async def dashboard_summary():
    now = time.time()
    one_hour_ago = now - 3600
    last_hour = [e for e in DASHBOARD["events"] if e[0] >= one_hour_ago]
    avg_latency = None
    if DASHBOARD["latencies_ms"]:
        avg_latency = round(sum(DASHBOARD["latencies_ms"]) / len(DASHBOARD["latencies_ms"]), 1)

    top_lang = sorted(DASHBOARD["lang_counter"].items(), key=lambda x: x[1], reverse=True)[:5]
    top_topic = sorted(DASHBOARD["topic_counter"].items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "started_at": DASHBOARD["started_at"],
        "messages_total": DASHBOARD["messages_total"],
        "messages_last_hour": len(last_hour),
        "avg_latency_ms": avg_latency,
        "languages": [{"name": k, "count": v} for k, v in top_lang],
        "topics": [{"name": k, "count": v} for k, v in top_topic],
    }

@app.get("/dashboard/activity")
async def dashboard_activity():
    return {"recent": list(DASHBOARD["recent"])}

# ----- 헬스체크 -----
@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/admin/database/status")
async def database_status():
    """데이터베이스 상태 확인 (관리자용)"""
    try:
        size_mb = get_database_size()
        
        # 데이터베이스 연결로 간단한 쿼리 실행
        from database import SessionLocal, Message, Conversation, User
        db = SessionLocal()
        try:
            message_count = db.query(Message).count()
            conversation_count = db.query(Conversation).count()
            user_count = db.query(User).count()
        finally:
            db.close()
        
        return {
            "database_size_mb": size_mb,
            "message_count": message_count,
            "conversation_count": conversation_count,
            "user_count": user_count,
            "status": "healthy" if size_mb < 50 else "warning" if size_mb < 100 else "critical"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

@app.post("/admin/database/cleanup")
async def manual_cleanup():
    """수동 데이터베이스 정리 (관리자용)"""
    try:
        run_database_cleanup()
        return {"message": "데이터베이스 정리 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정리 실패: {str(e)}")


# === 예외 처리 핸들러 (CORS 헤더 포함) ===
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리 - CORS 헤더 포함"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리 - CORS 헤더 포함"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS", 
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

if __name__ == "__main__":
    import os, sys
    from pathlib import Path
    import uvicorn

    # 프로젝트 루트를 sys.path에 추가하여 "backend.simple_main"을 인식시킴
    root = Path(__file__).resolve().parent.parent  # repo root
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)  # 직접 app 객체 전달