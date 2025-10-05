import React, { useState, useRef, useEffect, memo } from "react";
import { Send, User, Loader2 } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ragMarkdown } from "../config/api";

interface Message {
  id: string;
  content: string;
  sender: "user" | "assistant";
  timestamp: string;
  loading?: boolean;
  detectedLanguage?: string;
}

interface ChatAreaProps {
  onMessageSent?: (message: string) => void;
  serverConnected?: boolean;
}

// 답변 텍스트 추출 유틸(파일 상단 혹은 컴포넌트 밖에 배치)
function extractAnswer(data: any): string {
  // 먼저 데이터가 객체인지 확인
  if (typeof data === 'string') {
    return data;
  }
  
  // JSON 응답에서 response 필드 우선 추출 (ChatResponse 모델 기준)
  if (data?.response) {
    return data.response;
  }
  
  // 다른 가능한 필드들 확인
  return (
    data?.answer ??
    data?.text ??
    data?.message ??
    data?.output ??
    data?.choices?.[0]?.message?.content ??
    JSON.stringify(data) // 마지막 fallback으로 전체 JSON을 문자열로 변환
  );
}

export default function ChatArea({ onMessageSent, serverConnected = false }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "안녕하세요! 저는 MARS입니다. 미세중력 실험, 우주 환경에서의 생명체 연구, 우주 생물학 데이터에 대해 궁금한 것이 있으면 언제든 질문해주세요!",
      sender: "assistant",
      timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: true })
    }
  ]);
  
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(() => `conv_${Date.now()}`);
  const [sessionId] = useState(() => {
    // 로컬스토리지에서 세션 ID 가져오기 또는 생성
    let sid = localStorage.getItem('user_session_id');
    if (!sid) {
      sid = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('user_session_id', sid);
    }
    return sid;
  });
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatListRef = useRef<HTMLDivElement>(null);

  // 대화 불러오기 함수 (외부에서 호출 가능하도록)
  const loadConversation = (conversationData: any) => {
    if (conversationData && conversationData.messages) {
      // 초기 환영 메시지 + 불러온 메시지
      const welcomeMessage: Message = {
        id: "1",
        content: "안녕하세요! 저는 MARS입니다. 미세중력 실험, 우주 환경에서의 생명체 연구, 우주 생물학 데이터에 대해 궁금한 것이 있으면 언제든 질문해주세요!",
        sender: "assistant",
        timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: true })
      };
      
      const loadedMessages = conversationData.messages.map((msg: any) => ({
        id: msg.id || Date.now().toString(),
        content: msg.content,
        sender: msg.sender,
        timestamp: msg.timestamp,
        detectedLanguage: msg.detectedLanguage
      }));
      
      setMessages([welcomeMessage, ...loadedMessages]);
      setConversationId(conversationData.id);
    }
  };

  // 전역에서 접근 가능하도록 window 객체에 등록
  useEffect(() => {
    (window as any).loadChatConversation = loadConversation;
    return () => {
      delete (window as any).loadChatConversation;
    };
  }, []);

  // 대화 저장 함수
  const saveConversation = () => {
    if (messages.length <= 1) return; // 초기 메시지만 있으면 저장 안함
    
    const userMessages = messages.filter(m => m.sender === 'user');
    if (userMessages.length === 0) return;

    const firstUserMessage = userMessages[0].content;
    const title = firstUserMessage.length > 40 
      ? firstUserMessage.substring(0, 37) + '...'
      : firstUserMessage;

    const conversation = {
      id: conversationId,
      title,
      timestamp: new Date().toISOString(),
      messageCount: messages.length - 1, // 초기 메시지 제외
      messages: messages.filter(m => m.id !== "1") // 초기 메시지 제외
    };

    // 로컬스토리지에 저장
    const existingHistory = localStorage.getItem('chat_history');
    let history = existingHistory ? JSON.parse(existingHistory) : [];
    
    // 같은 ID가 있으면 업데이트, 없으면 추가
    const existingIndex = history.findIndex((h: any) => h.id === conversationId);
    if (existingIndex >= 0) {
      history[existingIndex] = conversation;
    } else {
      history.unshift(conversation); // 최신 것을 앞에 추가
    }

    // 최대 50개까지만 저장
    if (history.length > 50) {
      history = history.slice(0, 50);
    }

    localStorage.setItem('chat_history', JSON.stringify(history));
  };

  // 메시지가 추가될 때마다 자동으로 하단으로 스크롤 및 저장
  useEffect(() => {
    if (messages.length > 1 && chatListRef.current) {
      chatListRef.current.scrollTop = chatListRef.current.scrollHeight;
    }
    
    // 메시지가 변경될 때마다 대화 저장 (디바운싱)
    const timer = setTimeout(() => {
      saveConversation();
    }, 1000);

    return () => clearTimeout(timer);
  }, [messages]);





  // 자동 높이 조절 함수
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    }
  };

  // inputMessage가 변경될 때마다 높이 조절
  useEffect(() => {
    adjustTextareaHeight();
  }, [inputMessage]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    if (!serverConnected) {
      alert('FastAPI 서버가 연결되지 않았습니다. 서버를 시작하고 "서버 테스트" 버튼을 클릭하여 연결을 확인하세요.');
      return;
    }

    const messageToSend = inputMessage;
    const detectedLanguage = "auto"; // 백엔드에서 자동 감지하도록 위임
    
    // UI 업데이트
    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageToSend,
      sender: "user",
      timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: true }),
      detectedLanguage
    };
    setMessages((prev: Message[]) => [...prev, userMessage]);
    onMessageSent?.(messageToSend);
    setInputMessage("");
    setIsLoading(true);

    setTimeout(() => { if (textareaRef.current) textareaRef.current.style.height = '48px'; }, 0);

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: "분석 중입니다...",
      sender: "assistant",
      timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: true }),
      loading: true
    };
    setMessages((prev: Message[]) => [...prev, loadingMessage]);

    try {
      // Markdown 응답을 직접 받음
      const md = await ragMarkdown(messageToSend, {
        include_sources: true,
        include_figures: true,
        fig_max_images: 2,
        fig_caption_max_chars: 0,
      });

      if (!md || md.trim() === "") {
        throw new Error("서버에서 빈 응답을 받았습니다.");
      }

      setMessages((prev: Message[]) => prev.map((msg: Message) =>
        msg.id === loadingMessage.id
          ? { ...msg, content: md, loading: false }
          : msg
      ));
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev: Message[]) => prev.map((msg: Message) =>
        msg.id === loadingMessage.id
          ? { ...msg, content: `죄송합니다. 오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`, loading: false }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
    // Shift + Enter는 기본 동작(줄바꿈) 허용
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="flex-1 p-4 overflow-y-auto" ref={chatListRef}>
        <div className="space-y-4 max-w-6xl mx-auto pt-24">
          {messages.map((message: Message, index) => (
            <div
              key={`${message.id}-${index}`}
              className={`flex gap-3 ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.sender === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center mt-1">
                  {message.loading ? (
                    <Loader2 className="w-4 h-4 text-white animate-spin" />
                  ) : (
                    <div className="w-5 h-5 rounded-full bg-red-600 relative">
                      <div className="absolute w-1 h-1 bg-red-800 rounded-full top-1.5 left-1"></div>
                      <div className="absolute w-1.5 h-1.5 bg-red-800 rounded-full top-1 right-1"></div>
                      <div className="absolute w-1 h-1 bg-red-800 rounded-full bottom-1.5 left-1.5"></div>
                    </div>
                  )}
                </div>
              )}
              
              <div
                className={`max-w-4xl p-5 rounded-lg ${
                  message.sender === "user"
                    ? "bg-blue-500 text-white max-w-2xl"
                    : "bg-white text-gray-800 border border-gray-200 shadow-sm"
                }`}
              >
                {message.sender === "assistant" ? (
                  // AI 응답은 Markdown으로 렌더링 (will-change로 리페인트 최적화)
                  <div className="markdown-content" style={{ willChange: 'auto' }}>
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({node, ...props}) => <h1 className="text-2xl font-bold mb-4 mt-5 text-gray-800" {...props} />,
                        h2: ({node, ...props}) => <h2 className="text-xl font-semibold mb-3 mt-4 text-gray-700" {...props} />,
                        h3: ({node, ...props}) => <h3 className="text-lg font-medium mb-3 mt-3 text-gray-600" {...props} />,
                        p: ({node, ...props}) => <p className="mb-4 text-gray-700 leading-relaxed text-base" {...props} />,
                        strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                        em: ({node, ...props}) => <em className="italic text-gray-700" {...props} />,
                        ul: ({node, ...props}) => <ul className="list-disc list-inside mb-4 space-y-2" {...props} />,
                        ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-4 space-y-2" {...props} />,
                        li: ({node, ...props}) => <li className="text-gray-700 ml-2 text-base" {...props} />,
                        blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-400 pl-4 py-3 my-4 bg-blue-50 rounded-r-lg text-gray-700" {...props} />,
                        code: ({node, inline, ...props}: any) => 
                          inline 
                            ? <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-red-600" {...props} />
                            : <code className="block bg-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto my-3" {...props} />,
                        a: ({node, ...props}) => <a className="text-blue-600 hover:underline text-base" target="_blank" rel="noopener noreferrer" {...props} />,
                        img: ({node, src, alt, ...props}) => (
                          <div className="my-4 flex justify-center bg-gray-100 rounded-lg overflow-hidden" style={{ minHeight: '200px' }}>
                            <img 
                              src={src}
                              alt={alt || '이미지'}
                              className="max-w-full max-h-96 w-auto h-auto object-contain" 
                              loading="lazy"
                              onError={(e) => {
                                const target = e.currentTarget;
                                target.style.display = 'none';
                                const parent = target.parentElement;
                                if (parent) {
                                  parent.innerHTML = '<div class="p-4 text-gray-500 text-sm">이미지를 불러올 수 없습니다</div>';
                                }
                              }}
                              {...props} 
                            />
                          </div>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  // 사용자 메시지는 일반 텍스트
                  <p className="whitespace-pre-wrap text-base">{message.content}</p>
                )}
                <div className={`text-sm mt-3 ${
                  message.sender === "user" ? "text-blue-100" : "text-gray-500"
                }`}>
                  <span>{message.timestamp}</span>
                </div>
              </div>

              {message.sender === "user" && (
                <div className="flex-shrink-0 w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="p-5 border-t border-gray-200 flex-shrink-0 bg-white">
        <div className="max-w-4xl mx-auto relative">
          <textarea
            ref={textareaRef}
            value={inputMessage}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="MARS에게 물어보기..."
            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-3 pr-14 shadow-sm focus:border-blue-500 focus:ring-blue-500 resize-none min-h-[48px] text-base overflow-hidden"
            disabled={isLoading}
            style={{ minHeight: '48px' }}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-500 hover:bg-blue-600 text-white disabled:bg-gray-400 p-2 rounded-lg flex-shrink-0 transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}