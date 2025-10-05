// API 설정
const getBaseUrl = () => {
  // 개발 환경에서는 로컬 서버 우선 사용
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  
  // Vite 환경변수 접근
  const envApiUrl = import.meta.env.VITE_API_URL;
  
  // 환경 변수가 제대로 설정되었는지 확인
  if (envApiUrl && envApiUrl.startsWith('http')) {
    console.log('✅ Using API URL from env:', envApiUrl);
    return envApiUrl;
  }
  
  // Fallback: Railway production URL
  const fallbackUrl = 'https://hackaton-pj-production.up.railway.app';
  console.warn('⚠️ VITE_API_URL not set, using fallback:', fallbackUrl);
  return fallbackUrl;
};

export const API_CONFIG = {
  BASE_URL: getBaseUrl(),
  
  ENDPOINTS: {
    INIT: '/',
    CHAT: '/chat',
    RAG_MD: '/rag/md',
    STATS: '/data/stats',
    GLOBAL_STATS: '/data/global-stats',
    RECENT_ACTIVITY: '/data/recent-activity',
    HEALTH: '/health',
    TEST: '/health'
  }
};

export const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// --- RAG Markdown API ---
export type RagMdOptions = {
  include_sources?: boolean;
  include_figures?: boolean;
  fig_max_images?: number;
  fig_caption_max_chars?: number;
};

export const ragMarkdown = async (
  question: string,
  options: RagMdOptions = {}
): Promise<string> => {
  const url = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.RAG_MD}`;
  const payload = {
    question,
    include_sources: true,
    include_figures: true,
    fig_max_images: 2,
    fig_caption_max_chars: 0,
    ...options,
  };

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.text().catch(() => '');
    throw new Error(`RAG MD failed: ${res.status} ${res.statusText} ${err}`.trim());
  }

  // Expect text/markdown; fallback to text if content-type missing
  return await res.text();
};