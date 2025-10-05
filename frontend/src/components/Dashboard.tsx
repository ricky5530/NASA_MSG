import React, { useState, useEffect } from "react";
import { 
  Activity, 
  MessageSquare, 
  Clock, 
  TrendingUp, 
  Globe,
  BarChart3,
  RefreshCw
} from "lucide-react";
import { API_CONFIG } from "../config/api";

interface DashboardSummary {
  started_at: string;
  messages_total: number;
  messages_last_hour: number;
  avg_latency_ms: number | null;
  languages: { name: string; count: number }[];
  topics: { name: string; count: number }[];
}

interface RecentActivity {
  ts: string;
  language: string;
  topic: string;
  text: string;
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activity, setActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [summaryRes, activityRes] = await Promise.all([
        fetch(`${API_CONFIG.BASE_URL}/dashboard/summary`),
        fetch(`${API_CONFIG.BASE_URL}/dashboard/activity`)
      ]);

      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
      }

      if (activityRes.ok) {
        const activityData = await activityRes.json();
        setActivity(activityData.recent || []);
      }
    } catch (error) {
      console.error("Dashboard fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const startUserSession = async () => {
    try {
      // 세션 ID 생성 (localStorage에서 가져오거나 새로 생성)
      let sessionId = localStorage.getItem('user-session-id');
      if (!sessionId) {
        sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('user-session-id', sessionId);
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/user/session/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': sessionId
        },
        body: JSON.stringify({})
      });

      if (response.ok) {
        const sessionData = await response.json();
        console.log('User session started:', sessionData);
        localStorage.setItem('user-id', sessionData.user_id);
      }
    } catch (error) {
      console.error("Session start error:", error);
    }
  };

  useEffect(() => {
    // 페이지 로드 시 사용자 세션 시작
    startUserSession();
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 5000); // 5초마다 갱신

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
      portuguese: '🇵🇹',
      russian: '🇷🇺',
      hindi: '🇮🇳',
      arabic: '🇸🇦',
      unknown: '🌐'
    };
    return emojiMap[lang] || '🌐';
  };

  const getTopicColor = (topic: string) => {
    const colorMap: { [key: string]: string } = {
      microgravity: 'bg-purple-100 text-purple-700',
      radiation: 'bg-red-100 text-red-700',
      plant_growth: 'bg-green-100 text-green-700',
      bone_density: 'bg-blue-100 text-blue-700',
      microbiome: 'bg-yellow-100 text-yellow-700',
      cardio: 'bg-pink-100 text-pink-700',
      stem_cell: 'bg-indigo-100 text-indigo-700',
      iss: 'bg-cyan-100 text-cyan-700',
      general: 'bg-gray-100 text-gray-700'
    };
    return colorMap[topic] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
          <span className="text-gray-600">대시보드 로딩 중...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 overflow-y-auto">
      <div className="p-6 max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
              <BarChart3 className="w-10 h-10 text-blue-500" />
              MARS 대시보드
            </h1>
            <p className="text-lg text-gray-600 mt-2">실시간 사용 통계 및 분석</p>
          </div>
          
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-5 py-3 rounded-lg flex items-center gap-2 transition-colors text-base ${
              autoRefresh 
                ? 'bg-blue-500 text-white hover:bg-blue-600' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <RefreshCw className={`w-5 h-5 ${autoRefresh ? 'animate-spin' : ''}`} />
            자동 갱신 {autoRefresh ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* 주요 지표 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-medium text-gray-600">전체 메시지</h3>
              <MessageSquare className="w-6 h-6 text-purple-500" />
            </div>
            <p className="text-4xl font-bold text-gray-800">{summary?.messages_total || 0}</p>
            <p className="text-sm text-gray-500 mt-2">누적 대화 수</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-medium text-gray-600">최근 1시간</h3>
              <Activity className="w-6 h-6 text-orange-500" />
            </div>
            <p className="text-4xl font-bold text-gray-800">{summary?.messages_last_hour || 0}</p>
            <p className="text-sm text-gray-500 mt-2">메시지 활동</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-medium text-gray-600">평균 응답 시간</h3>
              <Clock className="w-6 h-6 text-red-500" />
            </div>
            <p className="text-4xl font-bold text-gray-800">
              {summary?.avg_latency_ms ? `${summary.avg_latency_ms}ms` : 'N/A'}
            </p>
            <p className="text-sm text-gray-500 mt-2">AI 응답 속도</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-medium text-gray-600">지원 언어</h3>
              <Globe className="w-6 h-6 text-indigo-500" />
            </div>
            <p className="text-4xl font-bold text-gray-800">15+</p>
            <p className="text-sm text-gray-500 mt-2">다국어 대응</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 언어 분포 */}
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-5 flex items-center gap-2">
              <Globe className="w-6 h-6 text-blue-500" />
              언어별 사용량
            </h3>
            <div className="space-y-4">
              {summary?.languages.slice(0, 5).map((lang, idx) => {
                const maxCount = summary.languages[0]?.count || 1;
                const percentage = (lang.count / maxCount) * 100;
                
                return (
                  <div key={idx}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-base font-medium text-gray-700 flex items-center gap-2">
                        <span>{getLanguageEmoji(lang.name)}</span>
                        <span className="capitalize">{lang.name}</span>
                      </span>
                      <span className="text-base text-gray-600">{lang.count}회</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-blue-500 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 토픽 분포 */}
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-5 flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-green-500" />
              인기 토픽
            </h3>
            <div className="space-y-4">
              {summary?.topics.slice(0, 5).map((topic, idx) => {
                const maxCount = summary.topics[0]?.count || 1;
                const percentage = (topic.count / maxCount) * 100;
                const rawName = (topic && (topic as any).name) ?? '';
                const safeName = String(rawName || '') as string;
                const label = safeName ? safeName.replace(/_/g, ' ') : 'N/A';
                const color = getTopicColor(safeName || 'general');

                return (
                  <div key={idx}>
                    <div className="flex justify-between items-center mb-2">
                      <span className={`text-base font-medium px-3 py-2 rounded ${color}`}>
                        {label}
                      </span>
                      <span className="text-base text-gray-600">{topic.count}회</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-green-500 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* 최근 활동 로그 */}
        <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-5 flex items-center gap-2">
            <Activity className="w-6 h-6 text-purple-500" />
            최근 활동 ({activity.length})
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {activity.map((item, idx) => {
              const topicRaw = (item as any)?.topic ?? '';
              const topicStr = topicRaw ? String(topicRaw) : '';
              const showBadge = !!topicStr;
              const label = topicStr ? topicStr.replace(/_/g, ' ') : '';
              const color = getTopicColor(topicStr || 'general');

              return (
                <div 
                  key={idx} 
                  className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-xl">
                    {getLanguageEmoji(item.language)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      {showBadge && (
                        <span className={`text-sm px-3 py-1 rounded font-medium ${color}`}>
                          {label}
                        </span>
                      )}
                      <span className="text-sm text-gray-500">
                        {formatDate(item.ts)}
                      </span>
                    </div>
                    <p className="text-base text-gray-700 truncate">{item.text}</p>
                  </div>
                </div>
              );
            })}
            
            {activity.length === 0 && (
              <div className="text-center py-8 text-gray-500 text-base">
                아직 활동 기록이 없습니다
              </div>
            )}
          </div>
        </div>

        {/* 시스템 정보 */}
        {summary?.started_at && (
          <div className="mt-6 text-center text-base text-gray-500">
            서버 시작: {formatDate(summary.started_at)}
          </div>
        )}
      </div>
    </div>
  );
}