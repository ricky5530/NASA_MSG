# 🏆 해커톤 AI 챗봇 프로젝트 - 셋업 가이드

## 📁 프로젝트 구조 개요
```
hackathon-project/
├── backend/                 # FastAPI 백엔드
│   ├── main.py             # 메인 서버 파일 (NASA 프로젝트에서 복사됨)
│   ├── requirements.txt    # Python 의존성
│   └── services/           # 서비스 로직
│       └── chat_service.py # 채팅 서비스 (현재 OpenAI 기반)
├── frontend/               # React + TypeScript 프론트엔드
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatArea.tsx # 메인 채팅 UI
│   │   ├── config/
│   │   │   └── api.ts      # API 설정 파일
│   │   └── styles/
│   │       └── globals.css # 스타일 파일
│   ├── package.json        # Node.js 의존성
│   ├── vite.config.ts      # Vite 빌드 도구 설정
│   └── index.html          # HTML 템플릿
└── README.md              # 이 파일
```

## ✅ 환경 설정 체크리스트

### 1️⃣ 백엔드 환경 설정
```bash
cd backend

# Python 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
# OPENAI_API_KEY=your_openai_api_key_here
```

### 2️⃣ 프론트엔드 환경 설정
```bash
cd frontend

# Node.js 의존성 설치
npm install

# 개발 서버 실행 테스트
npm run dev
```

### 3️⃣ 연동 테스트
- [ ] 백엔드 서버 실행: `python main.py` (포트 8000)
- [ ] 프론트엔드 실행: `npm run dev` (포트 3000 또는 5173)
- [ ] 브라우저에서 http://localhost:3000 접속
- [ ] 채팅 메시지 전송 테스트

## 🤖 AI 모델 통합 로드맵

### Phase 1: 기본 구조 이해
- [ ] `backend/services/chat_service.py` 파일 분석
- [ ] 현재 OpenAI API 기반 응답 생성 로직 파악
- [ ] API 엔드포인트 구조 이해 (`/chat`, `/health`)

### Phase 2: 커스텀 모델 준비
- [ ] 학습된 모델 파일 준비 (.pkl, .pt, .bin 등)
- [ ] 모델 로딩에 필요한 라이브러리 확인
- [ ] `backend/models/` 디렉토리 생성 및 모델 파일 배치

### Phase 3: FAISS 벡터 DB 준비
- [ ] FAISS 라이브러리 설치: `pip install faiss-cpu`
- [ ] 벡터 인덱스 파일 준비
- [ ] 문서 데이터 JSON 파일 준비
- [ ] `backend/faiss_db/` 디렉토리 생성

### Phase 4: 서비스 교체
- [ ] 새로운 `CustomChatService` 클래스 생성
- [ ] 기존 `ChatService` 대신 사용하도록 `main.py` 수정
- [ ] 응답 형태 호환성 확인 (response 필드 유지)

## 🔧 커스텀 모델 통합 가이드

### 현재 ChatService 인터페이스
```python
# services/chat_service.py에서 확인
async def get_response(self, message: str, language: str = "auto") -> Dict[str, Any]:
    return {
        "answer": "응답 텍스트",           # 필수: 실제 응답
        "sources": [],                   # 선택: 참조 소스 목록
        "conversation_id": "uuid"        # 선택: 대화 ID
    }
```

### 교체할 CustomChatService 예시 구조
```python
class CustomChatService:
    def __init__(self):
        # 1. 커스텀 모델 로드
        self.model = load_custom_model("./models/your_model.pkl")
        
        # 2. FAISS 인덱스 로드
        self.faiss_index = faiss.read_index("./faiss_db/vectors.index")
        self.documents = load_documents("./faiss_db/documents.json")
        
        # 3. 임베딩 모델 로드
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def get_response(self, message: str, language: str = "auto"):
        # 1. FAISS에서 관련 문서 검색
        # 2. 커스텀 모델로 응답 생성
        # 3. 기존 형태로 반환
        pass
```

## 📋 개발 우선순위

### 🥇 High Priority (반드시 해야 할 것)
1. **모델 로딩 검증**: 커스텀 모델이 정상적으로 로드되는지 확인
2. **FAISS 검색 구현**: 사용자 질문에 관련된 문서 검색
3. **응답 생성 로직**: 검색된 문서 + 커스텀 모델로 응답 생성
4. **API 호환성**: 기존 `/chat` 엔드포인트와 동일한 응답 형태 유지

### 🥈 Medium Priority (시간 있으면)
1. **성능 최적화**: 응답 속도 개선
2. **에러 핸들링**: 모델/DB 오류 시 fallback 로직
3. **로깅 추가**: 디버깅용 로그 시스템

### 🥉 Low Priority (나중에)
1. **UI 개선**: 프론트엔드 디자인 수정
2. **추가 기능**: 대화 히스토리, 북마크 등

## 🚨 주의사항

### ⚠️ 건드리면 안 되는 것들
- `frontend/` 디렉토리는 건드리지 말 것 (이미 완성됨)
- `main.py`의 API 엔드포인트 구조 변경 금지
- ChatResponse 모델 구조 변경 금지

### ✅ 자유롭게 수정해도 되는 것들
- `services/chat_service.py` - 완전히 새로 작성 가능
- `requirements.txt` - 필요한 라이브러리 추가
- 새로운 서비스 파일 추가 (예: `custom_model_service.py`)

## 🔍 디버깅 팁

### 백엔드 로그 확인
```bash
# 서버 실행 시 상세 로그 출력
python main.py

# 특정 API 테스트
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "테스트 메시지", "language": "auto"}'
```

### 프론트엔드 디버깅
- 브라우저 개발자 도구 → Network 탭에서 API 호출 확인
- Console 탭에서 JavaScript 에러 확인

## 📞 도움이 필요할 때

1. **모델 로딩 이슈**: 모델 파일 형식, 라이브러리 버전 확인
2. **FAISS 문제**: 인덱스 파일 경로, 차원 수 확인
3. **API 연동 이슈**: 응답 형태, CORS 설정 확인

---

**🎯 목표**: 기존 OpenAI 기반 → 커스텀 모델 + FAISS DB 기반으로 교체하되, 프론트엔드는 전혀 수정하지 않고 그대로 사용하기!