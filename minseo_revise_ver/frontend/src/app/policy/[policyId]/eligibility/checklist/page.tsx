/**
 * Eligibility Checklist Page (화면 6)
 * 자격 확인 질문 화면 - Stitch 디자인 적용
 */

'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { answerEligibilityQuestion } from '@/lib/api';
import { useEligibilityStore } from '@/store/useEligibilityStore';
import { routes } from '@/lib/routes';

export default function EligibilityChecklistPage() {
  const params = useParams();
  const router = useRouter();
  const policyId = Number(params.policyId);
  
  const {
    sessionId,
    currentQuestion,
    progress,
    addAnswer,
    setQuestion,
    setLoading,
    loading,
  } = useEligibilityStore();
  
  // Redirect if no session
  React.useEffect(() => {
    if (!sessionId || !currentQuestion) {
      router.push(routes.eligibilityStart(policyId));
    }
  }, [sessionId, currentQuestion, policyId, router]);
  
  const handleAnswer = async (answer: string) => {
    if (!sessionId) return;
    
    try {
      setLoading(true);
      addAnswer(answer);
      
      const response = await answerEligibilityQuestion({
        session_id: sessionId,
        answer,
      });
      
      if (response.completed) {
        router.push(routes.eligibilityResult(policyId));
      } else if (response.question) {
        setQuestion(response.question, response.progress, response.options);
      }
      
    } catch (error) {
      console.error('Failed to answer question:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!currentQuestion || !progress) {
    return null;
  }
  
  // 옵션이 있는지 확인
  const options = currentQuestion.options || [];
  const questionText = typeof currentQuestion === 'string' ? currentQuestion : currentQuestion.question;
  
  return (
    <main className="flex-1 flex flex-col justify-center items-center px-4 py-8">
      <div className="w-full max-w-[640px] flex flex-col gap-6">
        {/* Progress Indicator Section */}
        <div className="flex flex-col gap-3 px-4">
          <div className="flex justify-between items-end">
            <div>
              <p className="text-primary font-bold text-xs uppercase tracking-widest mb-1">Eligibility Scan</p>
              <p className="text-[#111817] dark:text-gray-200 text-lg font-bold leading-normal">자격 확인 진행 중</p>
            </div>
            <p className="text-[#111817] dark:text-gray-400 text-sm font-semibold leading-normal">
              Step {progress?.current || 1} of {progress?.total || 10}
            </p>
          </div>
          <div className="h-2 w-full rounded-full bg-[#d5e2e0] dark:bg-gray-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${((progress?.current || 0) / (progress?.total || 1)) * 100}%` }}
            />
          </div>
        </div>
        
        {/* Question Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none border border-[#eaf0ef] dark:border-gray-700 p-8 flex flex-col gap-8">
          {/* Badge & Question */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-1.5 rounded-full">
              <span className="material-symbols-outlined text-[18px]">help_center</span>
              <span className="text-xs font-bold leading-none">자격 확인을 위해 필요해요</span>
            </div>
            <h1 className="text-[#111817] dark:text-white text-3xl font-extrabold tracking-tight leading-tight px-2">
              Q. {questionText}
            </h1>
          </div>
          
          {/* Options List */}
          {options.length > 0 ? (
            <div className="flex flex-col gap-3">
              {options.map((option, idx) => (
                <label
                  key={idx}
                  className="group flex items-center gap-4 rounded-xl border-2 border-solid border-[#d5e2e0] dark:border-gray-700 p-5 cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all"
                >
                  <input
                    type="radio"
                    name="answer"
                    value={option}
                    onChange={() => handleAnswer(option)}
                    disabled={loading}
                    className="h-6 w-6 border-2 border-[#d5e2e0] dark:border-gray-600 bg-transparent text-primary focus:outline-none focus:ring-0 focus:ring-offset-0 transition-all cursor-pointer disabled:opacity-50"
                  />
                  <div className="flex grow flex-col">
                    <p className="text-[#111817] dark:text-gray-200 text-base font-bold group-hover:text-primary transition-colors">
                      {option}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <input
                type="text"
                className="w-full px-4 py-3 border-2 border-[#d5e2e0] dark:border-gray-700 rounded-xl focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all dark:bg-gray-900 dark:text-white"
                placeholder="답변을 입력하세요..."
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                    handleAnswer(e.currentTarget.value.trim());
                    e.currentTarget.value = '';
                  }
                }}
                disabled={loading}
              />
            </div>
          )}
          
          {/* CTA Actions */}
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            {options.length === 0 && (
              <button
                onClick={(e) => {
                  const input = e.currentTarget.parentElement?.parentElement?.querySelector('input[type="text"]') as HTMLInputElement;
                  if (input?.value.trim()) {
                    handleAnswer(input.value.trim());
                    input.value = '';
                  }
                }}
                disabled={loading}
                className="flex-1 bg-primary hover:bg-primary/90 text-white font-bold h-14 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>다음 단계로</span>
                    <span className="material-symbols-outlined">arrow_forward</span>
                  </>
                )}
              </button>
            )}
            <button
              onClick={() => router.push(routes.policy(policyId))}
              disabled={loading}
              className="px-8 border-2 border-[#d5e2e0] dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-[#111817] dark:text-gray-200 font-bold h-14 rounded-xl transition-all disabled:opacity-50"
            >
              중단하고 홈으로
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

