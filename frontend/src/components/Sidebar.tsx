import React, { useState, useEffect } from "react";
import { 
  MessageSquare, 
  History, 
  BarChart3,
  Clock,
  TrendingUp,
  Globe,
  Activity,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Plus
} from "lucide-react";
import { API_CONFIG } from "../config/api";

interface SidebarProps {
  currentView: 'chat' | 'dashboard';
  onViewChange: (view: 'chat' | 'dashboard') => void;
}

interface ConversationHistory {
  id: string;
  title: string;
  timestamp: string;
  messageCount: number;
}

interface DashboardSummary {
  messages_total: number;
  messages_last_hour: number;
  avg_latency_ms: number | null;
  languages: { name: string; count: number }[];
  topics: { name: string; count: number }[];
}

export default function Sidebar({ currentView, onViewChange }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [conversations, setConversations] = useState<ConversationHistory[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);

  // 대화 기록 불러오기 (로컬스토리지)
  useEffect(() => {
    const loadConversations = () => {
      const saved = localStorage.getItem('chat_history');
      if (saved) {
        try {
          setConversations(JSON.parse(saved));
        } catch (e) {
          console.error('Failed to load conversations:', e);
        }
      }
    };
    loadConversations();
  }, []);

  // 대시보드 데이터 가져오기
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await fetch(`${API_CONFIG.BASE_URL}/dashboard/summary`);
        if (res.ok) {
          const data = await res.json();
          setDashboardData(data);
        }
      } catch (error) {
        console.error('Dashboard fetch error:', error);
      }
    };

    fetchDashboard();
    const interval = setInterval(fetchDashboard, 10000); // 10초마다 갱신
    return () => clearInterval(interval);
  }, []);

  const deleteConversation = (id: string) => {
    const updated = conversations.filter(c => c.id !== id);
    setConversations(updated);
    localStorage.setItem('chat_history', JSON.stringify(updated));
  };

  const loadConversation = (conv: ConversationHistory) => {
    // 먼저 채팅 뷰로 전환합니다.
    onViewChange('chat');

    // ChatArea 컴포넌트가 렌더링될 시간을 준 후, 전역 함수를 호출합니다.
    // 이렇게 하면 대시보드 뷰에서도 채팅 불러오기가 정상적으로 동작합니다.
    setTimeout(() => {
      if (!(window as any).loadChatConversation) return;
      (window as any).loadChatConversation(conv);
    }, 0);
  };

  const startNewConversation = () => {
    // 페이지 새로고침으로 새 대화 시작
    window.location.reload();
  };

  const getLanguageEmoji = (lang: string) => {
    const emojiMap: { [key: string]: string } = {
      korean: '🇰🇷',
      english: '🇺🇸',
      japanese: '🇯🇵',
      chinese: '🇨🇳',
      spanish: '🇪🇸',
      french: '🇫🇷',
      german: '🇩🇪',
    };
    return emojiMap[lang] || '🌐';
  };

  if (isCollapsed) {
    return (
      <div className="w-16 bg-gray-900 text-white flex flex-col items-center py-4 gap-4">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 hover:bg-gray-800 rounded transition-colors"
          title="사이드바 펼치기"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
        
        <button
          onClick={() => onViewChange('chat')}
          className={`p-3 rounded transition-colors ${
            currentView === 'chat' ? 'bg-blue-600' : 'hover:bg-gray-800'
          }`}
          title="채팅"
        >
          <MessageSquare className="w-5 h-5" />
        </button>
        
        <button
          onClick={() => onViewChange('dashboard')}
          className={`p-3 rounded transition-colors ${
            currentView === 'dashboard' ? 'bg-blue-600' : 'hover:bg-gray-800'
          }`}
          title="대시보드"
        >
          <BarChart3 className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="w-80 bg-gray-900 text-white flex flex-col h-full overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between flex-shrink-0">
        <div className="flex-1">
          <h2 className="text-xl font-bold">MARS</h2>
          <p className="text-sm text-gray-400 mt-1">Mission for Astrobiology and Research Support</p>
        </div>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-1 hover:bg-gray-800 rounded transition-colors"
          title="사이드바 접기"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>

      {/* 뷰 전환 버튼 */}
      <div className="p-4 flex gap-2 flex-shrink-0">
        <button
          onClick={() => onViewChange('chat')}
          className={`flex-1 py-3 px-4 rounded flex items-center justify-center gap-2 transition-colors text-sm ${
            currentView === 'chat'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          <MessageSquare className="w-5 h-5" />
          채팅
        </button>
        <button
          onClick={() => onViewChange('dashboard')}
          className={`flex-1 py-3 px-4 rounded flex items-center justify-center gap-2 transition-colors text-sm ${
            currentView === 'dashboard'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          <BarChart3 className="w-5 h-5" />
          대시보드
        </button>
      </div>

      {/* 대시보드 요약 */}
      <div className="px-4 pb-3 border-b border-gray-700 flex-shrink-0">
        <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          실시간 통계
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">전체 메시지</div>
            <div className="text-xl font-bold">{dashboardData?.messages_total || 0}</div>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">최근 1시간</div>
            <div className="text-xl font-bold">{dashboardData?.messages_last_hour || 0}</div>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">평균 응답</div>
            <div className="text-base font-bold">
              {dashboardData?.avg_latency_ms ? `${dashboardData.avg_latency_ms}ms` : 'N/A'}
            </div>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">언어</div>
            <div className="text-base font-bold flex gap-1">
              {dashboardData?.languages.slice(0, 3).map((lang, idx) => (
                <span key={idx}>{getLanguageEmoji(lang.name)}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 인기 토픽 */}
      {dashboardData && dashboardData.topics.length > 0 && (
        <div className="px-4 py-3 border-b border-gray-700 flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            인기 토픽
          </h3>
          <div className="space-y-2">
            {dashboardData.topics.slice(0, 3).map((topic, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{topic.name.replace(/_/g, ' ')}</span>
                <span className="text-blue-400 font-semibold">{topic.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 대화 기록 */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="px-4 py-3 flex items-center justify-between border-b border-gray-700 flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-400 flex items-center gap-2">
            <History className="w-4 h-4" />
            대화 기록 ({conversations.length})
          </h3>
          <button
            onClick={startNewConversation}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
            title="새 대화 시작"
          >
            <Plus className="w-5 h-5 text-green-400" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto px-4 py-2 sidebar-scrollbar">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              저장된 대화가 없습니다
            </div>
          ) : (
            <div className="space-y-2">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => loadConversation(conv)}
                  className="bg-gray-800 rounded p-3 hover:bg-gray-700 transition-colors cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-white truncate">
                        {conv.title}
                      </h4>
                      <div className="flex items-center gap-2 mt-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-400">
                          {new Date(conv.timestamp).toLocaleDateString('ko-KR')}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {conv.messageCount}개 메시지
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-600 rounded transition-all"
                      title="삭제"
                    >
                      <Trash2 className="w-5 h-5 text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 푸터 */}
      <div className="p-4 border-t border-gray-700 flex-shrink-0">
        <div className="text-sm text-gray-500 text-center">
          <div>MARS</div>
          <div className="text-gray-600 mt-1">made by Team MSG</div>
        </div>
      </div>
    </div>
  );
}