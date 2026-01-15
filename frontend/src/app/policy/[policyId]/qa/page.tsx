/**
 * Policy Q&A Page (화면 5-1)
 * 정책 Q&A 채팅 화면 - Stitch 디자인 적용
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { sendChatMessageStream, initPolicy, initWebPolicy, cleanupSession } from '@/lib/api';
import { useSessionStore } from '@/store/useSessionStore';
import { routes } from '@/lib/routes';
import type { ChatMessage } from '@/lib/types';

// Parse citations in answer text
const parseCitations = (
  text: string,
  evidence: any[],
  policyId: number
): string => {
  if (!text) return '';
  
  let parsedText = text;
  
  // Step 1: Convert markdown links [text](url) to HTML links
  parsedText = parsedText.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
    (match, linkText, url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-primary font-medium hover:underline cursor-pointer">${linkText}</a>`;
    }
  );
  
  // Step 2: Parse mixed format: [정책문서 X, 웹 Y, Z] → split and process separately
  parsedText = parsedText.replace(
    /\[([^\]]+)\]/g,
    (match, content) => {
      const parts: string[] = [];
      
      // Check if it contains "정책문서"
      const policyMatch = content.match(/정책문서\s*([\d,\s]+)/);
      if (policyMatch) {
        const nums = policyMatch[1].split(',').map((n: string) => n.trim()).filter(Boolean);
        const links = nums.map((num: string) => {
          return `<a href="/policy/${policyId}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-primary font-semibold hover:underline cursor-pointer">
            <span class="material-symbols-outlined text-[14px]">article</span>정책문서 ${num}
          </a>`;
        }).join(', ');
        parts.push(links);
      }
      
      // Check if it contains "웹" or "웹 검색"
      const webMatch = content.match(/웹(?:\s*검색)?\s*([\d,\s]+)/);
      if (webMatch) {
        const nums = webMatch[1].split(',').map((n: string) => parseInt(n.trim()) - 1).filter(n => !isNaN(n));
        const links = nums.map((idx: number) => {
          const webEvidence = evidence.filter(e => e.type === 'web')[idx];
          if (webEvidence && webEvidence.url) {
            return `<a href="${webEvidence.url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-green-600 font-semibold hover:underline cursor-pointer">
              <span class="material-symbols-outlined text-[14px]">language</span>웹 검색 ${idx + 1}
            </a>`;
          }
          return `웹 검색 ${idx + 1}`;
        }).join(', ');
        parts.push(links);
      }
      
      // If no matches found, return original
      if (parts.length === 0) {
        return match;
      }
      
      return `[${parts.join(', ')}]`;
    }
  );
  
  return parsedText;
};

export default function PolicyQAPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const policyIdParam = params.policyId as string;
  const isWebPolicy = policyIdParam === 'web';
  const policyId = isWebPolicy ? 0 : Number(policyIdParam);
  
  // 웹 공고 파라미터 (URL 또는 sessionStorage에서)
  const [webData, setWebData] = useState<{
    webId: string;
    title: string;
    url: string;
    content: string;
  }>({
    webId: '',
    title: '',
    url: '',
    content: ''
  });

  useEffect(() => {
    if (isWebPolicy) {
      const webIdFromUrl = searchParams.get('webId') || '';
      
      // 1. sessionStorage에서 먼저 확인
      const storedData = sessionStorage.getItem(`webPolicy_${webIdFromUrl}`);
      if (storedData) {
        try {
          const parsed = JSON.parse(storedData);
          console.log('✅ sessionStorage에서 웹 공고 데이터 로드:', parsed);
          setWebData(parsed);
          setIsLoadingWebData(false);
          return;
        } catch (error) {
          console.error('❌ sessionStorage 파싱 에러:', error);
        }
      }
      
      // 2. URL 파라미터에서 가져오기 (fallback)
      const urlData = {
        webId: webIdFromUrl,
        title: searchParams.get('title') || '',
        url: searchParams.get('url') || '',
        content: searchParams.get('content') || ''
      };
      console.log('⚠️ URL 파라미터에서 웹 공고 데이터 로드:', urlData);
      setWebData(urlData);
      setIsLoadingWebData(false);
    }
  }, [isWebPolicy, searchParams]);

  const webId = webData.webId;
  const webTitle = webData.title;
  const webUrl = webData.url;
  const webContent = webData.content;
  
  const { sessionId, setSessionId, generateSessionId } = useSessionStore();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [policyInitialized, setPolicyInitialized] = useState(false);
  const [isLoadingWebData, setIsLoadingWebData] = useState(isWebPolicy); // 웹 공고 로딩 상태
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // 세션 ID를 useRef로 안정적으로 관리
  const stableSessionIdRef = useRef<string | null>(null);
  
  // sessionStorage 키
  const STORAGE_KEY = isWebPolicy ? `qa_messages_web_${webId}` : `qa_messages_${policyId}`;
  
  // 페이지 로드 시: sessionStorage에서 메시지 복원
  useEffect(() => {
    const restoreMessages = () => {
      try {
        const savedMessages = sessionStorage.getItem(STORAGE_KEY);
        if (savedMessages) {
          const parsedMessages = JSON.parse(savedMessages);
          if (parsedMessages.length > 0) {
            setMessages(parsedMessages);
          }
        }
      } catch (error) {
        console.error('Failed to restore messages:', error);
      }
    };
    
    // 초기 복원
    restoreMessages();
    
    // 페이지 visibility 변경 시에도 복원 (뒤로가기 등)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        restoreMessages();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [policyId, STORAGE_KEY]);
  
  // 메시지 변경 시: sessionStorage에 저장
  useEffect(() => {
    if (messages.length > 0) {
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
      } catch (error) {
        console.error('Failed to save messages:', error);
      }
    }
  }, [messages, STORAGE_KEY]);
  
  // 페이지 로드 시 정책 문서 캐시 초기화
  useEffect(() => {
    const initializePolicyCache = async () => {
      try {
        // 세션 ID가 없으면 생성 (한 번만 생성되도록 ref 사용)
        if (!stableSessionIdRef.current) {
          const currentSessionId = sessionId || generateSessionId();
          stableSessionIdRef.current = currentSessionId;
          if (!sessionId) {
            setSessionId(currentSessionId);
          }
        }
        
        // 정책 문서/웹 공고를 캐시에 로드
        if (isWebPolicy) {
          // 웹 공고 - webId가 있을 때만 초기화
          if (webId && webTitle && webUrl && webContent) {
            console.log('웹 공고 초기화 시작:', { webId, title: webTitle });
            await initWebPolicy(stableSessionIdRef.current, webId, webTitle, webUrl, webContent);
            setPolicyInitialized(true);
            console.log('웹 공고 초기화 완료');
          } else {
            console.warn('웹 공고 데이터가 아직 로드되지 않음:', { webId, webTitle, webUrl, contentLength: webContent.length });
          }
        } else {
          // DB 정책
          console.log('DB 정책 초기화 시작:', policyId);
          await initPolicy(stableSessionIdRef.current, policyId);
          setPolicyInitialized(true);
          console.log('DB 정책 초기화 완료');
        }
      } catch (error) {
        console.error('Failed to initialize policy cache:', error);
      }
    };
    
    initializePolicyCache();
    
    // 브라우저 닫을 때만 캐시 정리 (페이지 이동 시에는 유지!)
    const handleBeforeUnload = () => {
      if (stableSessionIdRef.current) {
        // 동기적으로 cleanup 요청 (브라우저 닫기 전)
        cleanupSession(stableSessionIdRef.current).catch(console.error);
        sessionStorage.removeItem(STORAGE_KEY);
        console.log('Cache cleaned up on browser close');
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [policyId, isWebPolicy, webId, webTitle, webUrl, webContent, sessionId, setSessionId]);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // 정책 reference 링크가 새 탭에서 열리도록 강제
  useEffect(() => {
    const handleCitationClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a');
      
      if (link && link.href && link.href.startsWith(window.location.origin)) {
        // 정책 문서 링크 또는 내부 링크 - 새 탭에서 강제로 열기
        e.preventDefault();
        e.stopPropagation();
        window.open(link.href, '_blank', 'noopener,noreferrer');
      }
    };
    
    // 메시지 컨테이너에 이벤트 리스너 추가
    const messageContainer = document.querySelector('.messages-container');
    if (messageContainer) {
      messageContainer.addEventListener('click', handleCitationClick as EventListener);
      return () => {
        messageContainer.removeEventListener('click', handleCitationClick as EventListener);
      };
    }
  }, [messages]);
  
  const handleResetChat = () => {
    if (confirm('대화 내용을 초기화하시겠습니까?')) {
      setMessages([]);
      sessionStorage.removeItem(STORAGE_KEY);
    }
  };
  
  const handleSendMessage = async (e: React.FormEvent, isRetry: boolean = false) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;
    
    const message = inputMessage.trim();
    if (!isRetry) {
      setInputMessage('');
    }
    
    // Add user message (if not retry)
    if (!isRetry) {
      const userMessage: ChatMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      
      // Add placeholder for assistant message (streaming)
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }
    
    try {
      setLoading(true);
      
      let fullAnswer = '';
      let evidence: any[] = [];
      let cacheMissDetected = false;
      
      // Send streaming request
      await sendChatMessageStream(
        {
          session_id: stableSessionIdRef.current || undefined,
          message,
          policy_id: policyId,
        },
        {
          onChunk: (chunk: string) => {
            // 답변 청크를 실시간으로 추가
            fullAnswer += chunk;
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage.role === 'assistant') {
                lastMessage.content = fullAnswer;
              }
              return newMessages;
            });
          },
          onStatus: (status) => {
            // 상태 업데이트 (선택적으로 UI에 표시 가능)
            console.log('Status:', status.message);
          },
          onEvidence: (ev) => {
            // Evidence 수신
            evidence = ev;
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage.role === 'assistant') {
                lastMessage.evidence = evidence;
              }
              return newMessages;
            });
          },
          onError: async (error: any) => {
            console.error('Streaming error:', error);
            
            // 캐시 미스 감지 시 자동 재시도
            if (error.code === 'CACHE_MISS' && !isRetry) {
              cacheMissDetected = true;
              console.log('Cache miss detected, reinitializing policy...');
              
              try {
                // 정책 캐시 다시 초기화
                if (isWebPolicy) {
                  await initWebPolicy(stableSessionIdRef.current!, webId, webTitle, webUrl, webContent);
                } else {
                  await initPolicy(stableSessionIdRef.current!, policyId);
                }
                console.log('Policy reinitialized, retrying...');
                
                // 메시지 제거 (마지막 assistant 메시지)
                setMessages((prev) => prev.slice(0, -1));
                
                // 재시도
                setLoading(false);
                const retryEvent = { preventDefault: () => {} } as React.FormEvent;
                await handleSendMessage(retryEvent, true);
                return;
              } catch (retryError) {
                console.error('Failed to reinitialize policy:', retryError);
              }
            }
            
            // 일반 에러 처리
            if (!cacheMissDetected) {
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage.role === 'assistant') {
                  lastMessage.content = error.message || '죄송합니다. 메시지 전송 중 오류가 발생했습니다. 다시 시도해주세요.';
                }
                return newMessages;
              });
            }
          },
          onDone: () => {
            console.log('Streaming completed');
            setLoading(false);
          },
        }
      );
      
    } catch (error) {
      console.error('Failed to send message:', error);
      
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage.role === 'assistant') {
          lastMessage.content = '죄송합니다. 메시지 전송 중 오류가 발생했습니다. 다시 시도해주세요.';
        }
        return newMessages;
      });
      setLoading(false);
    }
  };
  
  // 웹 공고 데이터 로딩 중
  if (isLoadingWebData) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-text-muted">웹 공고를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="flex-1 flex flex-row max-w-[1200px] mx-auto w-full relative">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-64 flex-col border-r border-[#eaf0ef] dark:border-[#3a3f42] p-6 gap-8">
        <div className="flex flex-col gap-1">
          <h1 className="text-[#111817] dark:text-white text-base font-bold">Startup Policy AI</h1>
          <p className="text-text-muted text-xs font-medium uppercase tracking-wider">Small Business Support</p>
        </div>
        <nav className="flex flex-col gap-2">
          <div
            onClick={() => router.push(routes.search)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-muted hover:bg-[#eaf0ef] dark:hover:bg-[#2d3235] cursor-pointer transition-colors"
          >
            <span className="material-symbols-outlined text-[22px]">format_list_bulleted</span>
            <p className="text-sm font-medium">All Policies</p>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 cursor-pointer">
            <span className="material-symbols-outlined text-[22px]">chat_bubble</span>
            <p className="text-sm font-bold">Q&A History</p>
          </div>
        </nav>
      </aside>
      
      {/* Chat Section */}
      <section className="flex-1 flex flex-col min-w-0 bg-white dark:bg-[#23272a] shadow-sm m-4 rounded-xl overflow-hidden border border-[#eaf0ef] dark:border-[#3a3f42]">
        <div className="px-6 py-4 border-b border-[#eaf0ef] dark:border-[#3a3f42] flex items-center justify-between bg-white dark:bg-[#23272a]">
          <div>
            <h2 className="text-lg font-bold text-[#111817] dark:text-white">정책 Q&A</h2>
            <p className="text-xs text-text-muted dark:text-text-muted-light">
              📝 정책에 대해 질문하세요
            </p>
          </div>
          <div className="flex items-center gap-3">
            {messages.length > 0 && (
              <button
                onClick={handleResetChat}
                className="text-sm font-medium text-text-muted hover:text-[#111817] dark:hover:text-white flex items-center gap-1 hover:bg-[#eaf0ef] dark:hover:bg-[#2d3235] px-2 py-1 rounded-lg transition-colors"
                title="새 대화 시작"
              >
                <span className="material-symbols-outlined text-[18px]">refresh</span>
                <span className="hidden sm:inline">새 대화</span>
              </button>
            )}
            <button
              onClick={() => {
                if (isWebPolicy) {
                  window.open(webUrl, '_blank');
                } else {
                  window.open(routes.policy(policyId), '_blank');
                }
              }}
              className="text-sm font-bold text-primary flex items-center gap-1 hover:underline"
            >
              <span className="material-symbols-outlined text-[18px]">article</span>
              공고문 보기
            </button>
          </div>
        </div>
        
        {/* Messages */}
        <div className="messages-container flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-text-muted">
              <p>메시지를 입력하여 대화를 시작하세요.</p>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} gap-2 max-w-[85%] ${msg.role === 'user' ? 'self-end' : 'self-start'}`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {msg.role === 'assistant' && (
                      <div className="size-6 bg-[#eaf0ef] dark:bg-[#2d3235] rounded-full flex items-center justify-center text-primary">
                        <span className="material-symbols-outlined text-[14px]">bolt</span>
                      </div>
                    )}
                    <span className="text-[11px] font-bold text-text-muted uppercase tracking-tighter">
                      {msg.role === 'user' ? 'You' : 'AI Assistant'}
                    </span>
                  </div>
                  <div
                    className={`${
                      msg.role === 'user'
                        ? 'bg-primary text-white rounded-2xl rounded-tr-none'
                        : 'bg-[#f0f4f3] dark:bg-[#2d3235] text-[#111817] dark:text-[#f9fafa] rounded-2xl rounded-tl-none border border-[#e0e7e6] dark:border-[#3a3f42]'
                    } px-5 py-4 shadow-sm`}
                  >
                    {msg.role === 'assistant' ? (
                      <div 
                        className="text-[15px] leading-relaxed"
                        dangerouslySetInnerHTML={{
                          __html: parseCitations(msg.content, msg.evidence || [], policyId)
                        }}
                      />
                    ) : (
                      <p className="text-[15px] leading-relaxed">{msg.content}</p>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex items-start gap-2 max-w-[85%] self-start">
                  <div className="size-6 bg-[#eaf0ef] dark:bg-[#2d3235] rounded-full flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined text-[14px]">bolt</span>
                  </div>
                  <div className="bg-[#f0f4f3] dark:bg-[#2d3235] px-5 py-3 rounded-2xl">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-text-muted rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
          
          {messages.length > 0 && !isWebPolicy && (
            <div className="flex flex-col gap-3 mt-6 items-center">
              <button
                onClick={() => router.push(routes.eligibilityStart(policyId))}
                className="w-full max-w-sm flex items-center justify-center gap-2 bg-primary text-white px-6 py-4 rounded-xl font-bold text-sm shadow-md hover:brightness-110 transition-all active:scale-95"
              >
                <span className="material-symbols-outlined text-[20px]">verified_user</span>
                [내가 해당되는지 확인 ▶]
              </button>
            </div>
          )}
        </div>
        
        {/* Input */}
        <div className="p-4 bg-background-light dark:bg-[#1c1f22] border-t border-[#eaf0ef] dark:border-[#3a3f42]">
          <form onSubmit={handleSendMessage} className="relative flex items-center">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              className="w-full bg-white dark:bg-[#2d3235] border border-[#e0e7e6] dark:border-[#3a3f42] rounded-xl px-4 py-3.5 pr-14 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all dark:text-white"
              placeholder="정책에 대해 궁금한 점을 물어보세요..."
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="absolute right-2 p-2 bg-primary text-white rounded-lg hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[20px]">send</span>
            </button>
          </form>
          <div className="flex justify-center gap-4 mt-3">
            <span className="text-[10px] text-text-muted flex items-center gap-1">
              <span className="material-symbols-outlined text-[12px]">info</span>
              AI가 웹 정보를 포함해 답변을 생성하므로 사실 여부를 재확인하시기 바랍니다.
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}

