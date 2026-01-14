/**
 * ChatBubble Component
 * 채팅 말풍선 컴포넌트
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { clsx } from 'clsx';
import { ExternalLink, FileText, Globe } from 'lucide-react';
import type { ChatMessage } from '@/lib/types';

interface ChatBubbleProps {
  message: ChatMessage;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[70%] rounded-lg px-4 py-3',
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-100 text-gray-900'
        )}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        
        {/* Evidence (for assistant messages) */}
        {!isUser && message.evidence && message.evidence.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-300">
            <p className="text-xs font-semibold mb-2">📚 근거 자료:</p>
            <div className="space-y-2">
              {message.evidence.slice(0, 5).map((evidence, idx) => {
                // 웹 검색 근거인 경우 (source_id가 있는 경우)
                if (evidence.source_id) {
                  return (
                    <Link 
                      key={idx}
                      href={`/web-source/${evidence.source_id}`}
                      className="flex items-start gap-2 text-xs p-2 rounded bg-white/50 hover:bg-white transition-colors group"
                    >
                      <Globe className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 group-hover:text-primary line-clamp-1">
                          {evidence.title || '웹 검색 결과'}
                        </div>
                        <div className="text-gray-600 line-clamp-2 mt-0.5">
                          {evidence.content.slice(0, 100)}...
                        </div>
                      </div>
                      <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-primary flex-shrink-0 mt-1" />
                    </Link>
                  );
                }
                
                // DB 정책 근거인 경우
                return (
                  <div key={idx} className="flex items-start gap-2 text-xs p-2 rounded bg-blue-50/50">
                    <FileText className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-gray-700">
                      <span className="font-medium">정책 근거:</span> {evidence.content.slice(0, 100)}...
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        
        {message.timestamp && (
          <p className={clsx('text-xs mt-2', isUser ? 'text-primary-100' : 'text-gray-500')}>
            {new Date(message.timestamp).toLocaleTimeString('ko-KR')}
          </p>
        )}
      </div>
    </div>
  );
};

