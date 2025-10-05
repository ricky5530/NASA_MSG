/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // 필요시 다른 환경 변수 추가
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
