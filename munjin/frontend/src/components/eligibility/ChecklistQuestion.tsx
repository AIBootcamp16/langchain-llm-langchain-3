/**
 * ChecklistQuestion Component
 * 체크리스트 질문 컴포넌트
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/common/Button';

interface ChecklistQuestionProps {
  question: string;
  onAnswer: (answer: string) => void;
  disabled?: boolean;
}

export const ChecklistQuestion: React.FC<ChecklistQuestionProps> = ({
  question,
  onAnswer,
  disabled = false,
}) => {
  const [answer, setAnswer] = useState('');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim() && !disabled) {
      onAnswer(answer.trim());
      setAnswer('');
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">{question}</h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="답변을 입력하세요..."
          rows={4}
          disabled={disabled}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
        />
        
        <Button
          type="submit"
          disabled={disabled || !answer.trim()}
          size="lg"
          className="w-full"
        >
          다음
        </Button>
      </form>
    </div>
  );
};

