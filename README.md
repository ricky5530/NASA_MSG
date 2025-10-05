# 🚀 MARS - Mission for Astrobiology and Research Support

**NASA 우주 생물학 데이터 기반 AI 챗봇 서비스**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-nasamsg.vercel.app-blue?style=for-the-badge&logo=vercel)](https://nasamsg.vercel.app/)
[![Backend](https://img.shields.io/badge/Backend-Render-green?style=for-the-badge&logo=render)](https://nasa-msg.onrender.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **🌌 우주 생물학의 세계를 탐험하세요!**  
> MARS는 NASA의 우주 생물학 연구 데이터를 학습한 AI 챗봇으로, 미세중력 실험부터 우주 환경에서의 생명체 연구까지 전문적인 질문에 답변합니다.

## 🌟 프로젝트 개요

**🔗 라이브 서비스**: [nasamsg.vercel.app](https://nasamsg.vercel.app/)

MARS(Mission for Astrobiology and Research Support)는 NASA의 우주 생물학 연구 논문 607편을 학습한 전문 AI 챗봇입니다. 연구자, 학생, 그리고 우주 생물학에 관심 있는 모든 사람들이 쉽게 접근할 수 있는 지식 플랫폼을 제공합니다.

### 🎯 주요 특징

- **📚 전문 데이터**: NASA 우주 생물학 논문 607편 학습
- **🤖 지능형 RAG**: FAISS 벡터 검색 + OpenAI GPT 기반 답변
- **🌍 다국어 지원**: 15개 언어 자동 감지 및 응답
- **📊 실시간 대시보드**: 사용 통계 및 인기 주제 분석
- **💾 대화 히스토리**: 로컬 저장으로 개인정보 보호
- **📱 반응형 디자인**: 모든 디바이스에서 최적화된 경험

## 🚀 라이브 서비스

### 🌐 **서비스 접속**: [nasamsg.vercel.app](https://nasamsg.vercel.app/)

**MARS 챗봇이 지금 바로 서비스 중입니다!** 🚀  
[nasamsg.vercel.app](https://nasamsg.vercel.app/)에서 NASA 우주 생물학 전문 AI와 대화해보세요.

✨ **특징**:
- 🆓 **무료 사용** - 별도 회원가입 불필요
- 🌍 **웹 브라우저 접속** - 앱 설치 없이 즉시 이용
- 🤖 **전문 AI 상담** - 607편의 NASA 논문 학습 완료
- 🗣️ **다국어 지원** - 15개 언어 자동 감지 및 응답

#### 💡 사용 예시
- *"미세중력이 식물 성장에 미치는 영향은?"*
- *"우주정거장에서의 미생물 연구에 대해 알려주세요"*
- *"우주 환경이 인간의 골밀도에 미치는 영향은?"*
- *"Mars missions and astrobiology research"*

## 🏗️ 아키텍처

```
NASA_MSG/
├── frontend/          # React + TypeScript 프론트엔드
├── backend/           # FastAPI + Python 백엔드
├── README.md          # 이 파일
└── 기타 설정 파일들
```

### 🎨 프론트엔드 ([Vercel](https://vercel.com/))
- **React 18.2** + **TypeScript**
- **Vite** 빌드 시스템
- **Tailwind CSS** 스타일링
- **실시간 채팅 인터페이스**
- **통계 대시보드**

### ⚙️ 백엔드 ([Render](https://render.com/))
- **FastAPI** + **Python 3.10**
- **SQLite** 데이터베이스
- **FAISS** 벡터 검색
- **OpenAI GPT** API
- **LangChain** RAG 파이프라인

## 📊 데이터 & AI

### 🔬 학습 데이터
- **출처**: NASA 우주 생물학 연구 논문
- **규모**: 607편의 전문 논문
- **범위**: 미세중력, 우주 환경, 생명체 연구, 우주정거장 실험 등
- **처리**: 청크 분할 + 벡터 임베딩 (FAISS 인덱스)

### 🧠 AI 시스템
- **RAG (Retrieval-Augmented Generation)**: 정확한 정보 검색 + 자연어 생성
- **벡터 검색**: FAISS를 통한 고속 의미적 검색
- **언어 모델**: OpenAI GPT-4 기반 답변 생성
- **다국어**: 자동 언어 감지 및 번역

## 🛠️ 기술 스택

### Frontend
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind%20CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white)

### AI & Data
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-FF6B6B?style=flat-square&logo=meta&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)

### Deployment
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=white)

## 🚀 시작하기

### 🔧 로컬 개발 환경 설정

#### 1. 저장소 클론
```bash
git clone https://github.com/ricky5530/NASA_MSG.git
cd NASA_MSG
```

#### 2. 백엔드 설정
```bash
cd backend
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
echo "OPENAI_API_KEY=your_openai_api_key" > .env

# 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 프론트엔드 설정
```bash
cd frontend
npm install
npm run dev
```

#### 4. 브라우저에서 확인
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## 📚 API 문서

백엔드가 실행 중일 때 다음 주소에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 🔗 주요 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/rag/md` | POST | RAG 기반 질문 답변 |
| `/dashboard/summary` | GET | 사용 통계 요약 |
| `/dashboard/activity` | GET | 최근 활동 로그 |
| `/health` | GET | 서버 상태 확인 |

## 📊 모니터링 & 분석

### 📈 실시간 대시보드
- **전체 메시지 수**: 누적 대화 통계
- **최근 1시간 활동**: 실시간 사용량
- **평균 응답 시간**: AI 성능 모니터링
- **언어별 분포**: 다국어 사용 현황
- **인기 토픽**: 주요 관심 주제

### 🗄️ 데이터 관리
- **자동 정리**: 24시간 이상 된 데이터 자동 삭제
- **용량 관리**: SQLite 크기 모니터링 및 최적화
- **백업**: 주요 설정 및 인덱스 파일 Git LFS 관리

## 🔒 보안 & 개인정보

- **로컬 저장**: 대화 히스토리는 사용자 브라우저에만 저장
- **익명 사용**: 회원가입 없이 익명으로 이용 가능
- **데이터 정리**: 서버 데이터는 24시간 후 자동 삭제
- **CORS 설정**: 안전한 크로스 도메인 통신

## 🤝 기여하기

### 🐛 버그 리포트
이슈가 발견되면 [GitHub Issues](https://github.com/ricky5530/NASA_MSG/issues)에 리포트해주세요.

### 💡 기능 제안
새로운 기능 아이디어가 있으시면 언제든 제안해주세요!

### 🔧 개발 참여
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다.

## 👥 팀

**Team MSG** - NASA 우주 생물학 AI 챗봇 개발팀

## 🙏 감사의 말

- **NASA**: 우주 생물학 연구 데이터 제공
- **OpenAI**: GPT API 서비스
- **Vercel & Render**: 안정적인 호스팅 서비스
- **오픈소스 커뮤니티**: 훌륭한 도구들

---

## 🌌 **MARS와 함께 우주 생물학의 미래를 탐험해보세요!**

### 🔗 **지금 바로 체험하기** → [nasamsg.vercel.app](https://nasamsg.vercel.app/)

> 💫 **NASA 데이터로 학습한 전문 AI가 여러분의 우주 생물학 궁금증을 해결해드립니다**

---

<div align="center">

**Made with ❤️ by Team MSG**

*"Bridging the gap between space science and humanity"*

</div>