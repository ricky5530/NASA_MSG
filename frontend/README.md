# MARS Frontend

**Mission for Astrobiology and Research Support** - 우주 생물학 연구 지원 AI 챗봇의 프론트엔드 애플리케이션

## 🚀 프로젝트 개요

MARS는 NASA의 우주 생물학 연구 데이터를 기반으로 한 AI 챗봇 서비스입니다. 이 프론트엔드는 사용자가 우주 환경에서의 생명체 연구, 미세중력 실험, 우주 생물학 데이터에 대해 쉽게 질문하고 답변을 받을 수 있는 인터페이스를 제공합니다.

## 🛠 기술 스택

- **React 18.2** - 사용자 인터페이스 구축
- **TypeScript** - 타입 안전성 보장
- **Vite** - 빠른 개발 환경 및 빌드 도구
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **Lucide React** - 아이콘 라이브러리
- **React Markdown** - 마크다운 렌더링
- **Remark GFM** - GitHub Flavored Markdown 지원

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/          # React 컴포넌트
│   │   ├── ChatArea.tsx     # 메인 채팅 인터페이스
│   │   ├── Sidebar.tsx      # 사이드바 및 대화 히스토리
│   │   └── Dashboard.tsx    # 실시간 통계 대시보드
│   ├── config/
│   │   └── api.ts          # API 설정
│   ├── styles/
│   │   └── globals.css     # 전역 스타일
│   ├── App.tsx             # 메인 앱 컴포넌트
│   └── main.tsx           # 앱 진입점
├── dist/                   # 빌드된 파일들
├── public/                 # 정적 파일들
├── package.json           # 의존성 및 스크립트
├── tailwind.config.js     # Tailwind 설정
├── tsconfig.json          # TypeScript 설정
└── vite.config.ts         # Vite 설정
```

## 🚀 시작하기

### 필수 요구사항

- **Node.js** 18+ 
- **npm** 9+

### 설치 및 실행

1. **의존성 설치**
   ```bash
   npm install
   ```

2. **개발 서버 실행**
   ```bash
   npm run dev
   ```
   브라우저에서 `http://localhost:5173` 접속

3. **프로덕션 빌드**
   ```bash
   npm run build
   ```

4. **빌드 파일 미리보기**
   ```bash
   npm run preview
   ```

## 📝 주요 기능

### 💬 채팅 인터페이스
- **실시간 대화**: MARS AI와 실시간 채팅
- **마크다운 지원**: 풍부한 텍스트 형식으로 답변 표시
- **언어 감지**: 자동 언어 감지 및 다국어 지원
- **대화 저장**: 로컬스토리지에 대화 히스토리 자동 저장

### 📊 대시보드
- **실시간 통계**: 메시지 수, 응답 시간, 언어 분포
- **인기 토픽**: 자주 묻는 주제들 시각화
- **사용자 활동**: 최근 활동 로그 표시

### 🎨 사용자 인터페이스
- **반응형 디자인**: 모바일부터 데스크톱까지 최적화
- **다크 사이드바**: 전문적이고 모던한 디자인
- **직관적 네비게이션**: 채팅과 대시보드 간 쉬운 전환

## 🔧 환경 설정

### API 설정
`src/config/api.ts`에서 백엔드 API URL을 설정합니다:

```typescript
export const API_CONFIG = {
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'https://your-backend-url.render.com'
    : 'http://localhost:8000'
};
```

### 환경 변수
개발 환경에서 필요한 경우 `.env` 파일을 생성하여 환경 변수를 설정할 수 있습니다.

## 📱 컴포넌트 가이드

### ChatArea.tsx
- 메인 채팅 인터페이스
- 메시지 렌더링 및 입력 처리
- 대화 히스토리 관리

### Sidebar.tsx
- 네비게이션 및 브랜딩
- 대화 히스토리 목록
- 실시간 통계 요약

### Dashboard.tsx
- 상세 통계 대시보드
- 차트 및 데이터 시각화
- 사용자 활동 로그

## 🎨 스타일링

프로젝트는 **Tailwind CSS**를 사용하여 스타일링됩니다:

- **유틸리티 우선**: 빠른 개발과 일관성
- **반응형 디자인**: 모든 디바이스에서 최적화
- **커스텀 설정**: `tailwind.config.js`에서 테마 확장

## 📦 빌드 및 배포

### Vercel 배포
프로젝트는 Vercel에 배포되도록 구성되어 있습니다:

```bash
# Vercel CLI로 배포
vercel --prod
```

### 수동 배포
다른 플랫폼에 배포하려면:

1. 빌드 실행: `npm run build`
2. `dist/` 폴더를 웹 서버에 업로드

## 🔍 개발 가이드

### 코드 스타일
- **TypeScript**: 모든 컴포넌트에서 타입 안전성 보장
- **함수형 컴포넌트**: React Hooks 사용
- **명명 규칙**: camelCase (변수), PascalCase (컴포넌트)

### 상태 관리
- **React useState**: 로컬 상태 관리
- **로컬스토리지**: 대화 히스토리 영구 저장
- **API 통신**: fetch API 사용

## 🐛 문제 해결

### 일반적인 문제들

1. **포트 충돌**
   ```bash
   # 다른 포트 사용
   npm run dev -- --port 3000
   ```

2. **빌드 에러**
   ```bash
   # 의존성 재설치
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **TypeScript 에러**
   ```bash
   # 타입 체크
   npm run type-check
   ```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👥 팀 정보

**Team MSG** - NASA 우주 생물학 데이터 기반 AI 챗봇 개발팀

---

### 🌟 특별한 기능들

- **15+ 언어 지원**: 전 세계 연구자들을 위한 다국어 지원
- **실시간 통계**: 사용 패턴 및 인기 주제 실시간 모니터링
- **대화 히스토리**: 로컬 저장으로 개인정보 보호
- **반응형 디자인**: 모든 디바이스에서 완벽한 사용자 경험

**MARS와 함께 우주 생물학의 세계를 탐험해보세요!** 🚀🔬✨