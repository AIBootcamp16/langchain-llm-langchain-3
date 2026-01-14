/**
 * Policy Q&A Page (화면 5-1)
 * 정책 Q&A 채팅 화면 - Stitch 디자인 적용
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { sendChatMessage } from '@/lib/api';
import { useSessionStore } from '@/store/useSessionStore';
import { routes } from '@/lib/routes';
import type { ChatMessage } from '@/lib/types';

export default function PolicyQAPage() {
  const params = useParams();
  const router = useRouter();
  const policyId = Number(params.policyId);
  
  const { sessionId, setSessionId } = useSessionStore();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;
    
    const message = inputMessage.trim();
    setInputMessage('');
    
    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    
    try {
      setLoading(true);
      
      // Send to API
      const response = await sendChatMessage({
        session_id: sessionId || undefined,
        message,
        policy_id: policyId,
      });
      
      // Update session ID
      if (!sessionId) {
        setSessionId(response.session_id);
      }
      
      // Add assistant message
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        evidence: response.evidence,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Failed to send message:', error);
      
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: '죄송합니다. 메시지 전송 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };
  
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
          <button
            onClick={() => router.push(routes.policy(policyId))}
            className="text-sm font-bold text-primary flex items-center gap-1 hover:underline"
          >
            <span className="material-symbols-outlined text-[18px]">article</span>
            공고문 보기
          </button>
        </div>
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
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
                    <p className="text-[15px] leading-relaxed">{msg.content}</p>
                    {msg.evidence && msg.evidence.length > 0 && (
                      <div className="mt-4 space-y-2">
                        {msg.evidence.map((ev, i) => (
                          <button
                            key={i}
                            className="flex items-center gap-1.5 bg-white dark:bg-[#23272a] px-3 py-1.5 rounded-lg border border-primary/20 text-primary text-xs font-bold hover:bg-primary/5 transition-colors shadow-sm"
                          >
                            <span className="material-symbols-outlined text-[16px]">database</span>
                            [근거 {i + 1}]
                          </button>
                        ))}
                      </div>
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
          
          {messages.length > 0 && (
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

