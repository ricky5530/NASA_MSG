"""
SQLite 데이터베이스 설정 및 모델 정의
사용자 세션 추적 및 대화 기록 저장
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
from pathlib import Path

# 데이터베이스 경로 설정
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chat_data.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},  # SQLite용 설정
    echo=False  # SQL 로그 출력 (디버깅용, 프로덕션에서는 False)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# === 데이터베이스 모델 정의 ===

class User(Base):
    """사용자 테이블 - 고유 사용자 추적"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # UUID
    session_id = Column(String, index=True)  # 브라우저 세션 ID
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    preferred_language = Column(String, default="auto")
    is_active = Column(Boolean, default=True)
    
    # 관계: 한 사용자는 여러 대화를 가질 수 있음
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """대화 세션 테이블 - 각 대화 세션 추적"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, unique=True, index=True, nullable=False)  # UUID
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=True)  # 대화 제목 (첫 메시지에서 생성)
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    primary_language = Column(String, default="unknown")
    is_active = Column(Boolean, default=True)
    
    # 관계
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """메시지 테이블 - 모든 대화 메시지 저장"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True, nullable=False)  # UUID
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), nullable=False)
    content = Column(Text, nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow)
    detected_language = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=True)  # AI 응답 시간 (사용자 메시지는 null)
    topic = Column(String, nullable=True)  # 메시지 주제 분류
    
    # 관계
    conversation = relationship("Conversation", back_populates="messages")


class Analytics(Base):
    """분석 데이터 테이블 - 시간별/일별 통계"""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    hour = Column(Integer)  # 0-23
    total_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    most_common_language = Column(String, default="unknown")
    most_common_topic = Column(String, default="general")


# === 데이터베이스 초기화 함수 ===

def init_db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ 데이터베이스 초기화 완료: {DB_PATH}")


def get_db():
    """
    데이터베이스 세션 의존성 주입용 함수
    FastAPI 엔드포인트에서 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# === 유틸리티 함수 ===

def create_user(db, session_id: str = None) -> User:
    """새 사용자 생성"""
    user_id = str(uuid.uuid4())
    user = User(
        user_id=user_id,
        session_id=session_id or user_id,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user(db, session_id: str) -> User:
    """세션 ID로 사용자 찾기 또는 생성"""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        user = create_user(db, session_id)
    else:
        user.last_seen = datetime.utcnow()
        db.commit()
    return user


def create_conversation(db, user_id: str, title: str = None) -> Conversation:
    """새 대화 세션 생성"""
    conversation_id = str(uuid.uuid4())
    conversation = Conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        title=title,
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(conversation)
    
    # 사용자의 total_conversations 증가
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.total_conversations += 1
    
    db.commit()
    db.refresh(conversation)
    return conversation


def save_message(
    db, 
    conversation_id: str, 
    content: str, 
    sender: str,
    detected_language: str = None,
    latency_ms: float = None,
    topic: str = None
) -> Message:
    """메시지 저장"""
    message_id = str(uuid.uuid4())
    message = Message(
        message_id=message_id,
        conversation_id=conversation_id,
        content=content,
        sender=sender,
        timestamp=datetime.utcnow(),
        detected_language=detected_language,
        latency_ms=latency_ms,
        topic=topic
    )
    db.add(message)
    
    # 대화의 message_count 증가
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if conversation:
        conversation.message_count += 1
        conversation.updated_at = datetime.utcnow()
        
        # 대화 제목이 없으면 첫 사용자 메시지로 설정
        if not conversation.title and sender == "user":
            conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        # 평균 레이턴시 업데이트
        if latency_ms and sender == "assistant":
            if conversation.avg_latency_ms == 0:
                conversation.avg_latency_ms = latency_ms
            else:
                # 이동 평균 계산
                conversation.avg_latency_ms = (
                    conversation.avg_latency_ms * 0.7 + latency_ms * 0.3
                )
        
        # 사용자의 total_messages 증가
        user = db.query(User).filter(User.user_id == conversation.user_id).first()
        if user:
            user.total_messages += 1
    
    db.commit()
    db.refresh(message)
    return message


def get_user_stats(db, user_id: str) -> dict:
    """사용자 통계 조회"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).all()
    
    return {
        "user_id": user.user_id,
        "first_seen": user.first_seen,
        "last_seen": user.last_seen,
        "total_messages": user.total_messages,
        "total_conversations": len(conversations),
        "active_conversations": sum(1 for c in conversations if c.is_active)
    }


def get_conversation_history(db, conversation_id: str) -> dict:
    """대화 기록 조회"""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if not conversation:
        return None
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).all()
    
    return {
        "conversation_id": conversation.conversation_id,
        "title": conversation.title,
        "started_at": conversation.started_at,
        "message_count": conversation.message_count,
        "messages": [
            {
                "content": msg.content,
                "sender": msg.sender,
                "timestamp": msg.timestamp,
                "detected_language": msg.detected_language,
                "latency_ms": msg.latency_ms
            }
            for msg in messages
        ]
    }


def cleanup_old_data(hours_to_keep: int = 24):
    """오래된 데이터를 정리하여 데이터베이스 크기 관리"""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_to_keep)
        
        # 오래된 메시지 삭제
        old_messages = db.query(Message).filter(Message.timestamp < cutoff_time)
        deleted_messages = old_messages.count()
        old_messages.delete()
        
        # 메시지가 없는 대화 삭제
        empty_conversations = db.query(Conversation).filter(
            ~Conversation.conversation_id.in_(
                db.query(Message.conversation_id).distinct()
            )
        )
        deleted_conversations = empty_conversations.count()
        empty_conversations.delete()
        
        # 대화가 없는 사용자 삭제
        empty_users = db.query(User).filter(
            ~User.user_id.in_(
                db.query(Conversation.user_id).distinct()
            )
        )
        deleted_users = empty_users.count()
        empty_users.delete()
        
        db.commit()
        
        print(f"데이터 정리 완료: 메시지 {deleted_messages}개, 대화 {deleted_conversations}개, 사용자 {deleted_users}개 삭제")
        return {
            "deleted_messages": deleted_messages,
            "deleted_conversations": deleted_conversations,
            "deleted_users": deleted_users
        }
        
    except Exception as e:
        db.rollback()
        print(f"데이터 정리 중 오류: {e}")
        raise e
    finally:
        db.close()


def get_database_size():
    """데이터베이스 크기 확인 (MB 단위)"""
    try:
        size_bytes = DB_PATH.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except FileNotFoundError:
        return 0


def vacuum_database():
    """데이터베이스 VACUUM 실행으로 공간 재확보"""
    try:
        db = SessionLocal()
        db.execute("VACUUM")
        db.close()
        print("데이터베이스 VACUUM 완료")
    except Exception as e:
        print(f"VACUUM 중 오류: {e}")


# 앱 시작 시 자동 실행
if __name__ == "__main__":
    init_db()
    print("데이터베이스 테이블이 생성되었습니다.")
    print(f"현재 데이터베이스 크기: {get_database_size()}MB")
