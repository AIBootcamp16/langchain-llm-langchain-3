/**
 * Eligibility Start Page (화면 5-2)
 * 자격 확인 시작 화면 - Stitch 디자인 적용
 */

'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { startEligibilityCheck } from '@/lib/api';
import { useEligibilityStore } from '@/store/useEligibilityStore';
import { routes } from '@/lib/routes';

export default function EligibilityStartPage() {
  const params = useParams();
  const router = useRouter();
  const policyId = Number(params.policyId);
  
  const { setSession, setQuestion, setLoading, loading, error } = useEligibilityStore();
  
  const handleStart = async () => {
    try {
      setLoading(true);
      
      const response = await startEligibilityCheck({ policy_id: policyId });
      
      setSession(response.session_id, response.policy_id);
      setQuestion(response.question, response.progress, response.options);
      
      router.push(routes.eligibilityChecklist(policyId));
      
    } catch (error) {
      console.error('Failed to start eligibility check:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <main className="max-w-[1200px] mx-auto px-6 py-8">
      {/* Breadcrumbs */}
      <nav className="flex flex-wrap items-center gap-2 mb-12">
        <a className="text-text-muted hover:underline text-sm font-medium cursor-pointer" onClick={() => router.push(routes.home)}>
          Home
        </a>
        <span className="material-symbols-outlined text-sm text-text-muted">chevron_right</span>
        <a className="text-text-muted hover:underline text-sm font-medium cursor-pointer" onClick={() => router.push(routes.policy(policyId))}>
          Policy Detail
        </a>
        <span className="material-symbols-outlined text-sm text-text-muted">chevron_right</span>
        <span className="text-[#111817] dark:text-gray-300 text-sm font-medium">Eligibility Check</span>
      </nav>
      
      {/* Main Content Area */}
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-full max-w-[640px] text-center">
          {/* Hero Visual */}
          <div className="mb-8 relative inline-flex items-center justify-center">
            <div className="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-full blur-2xl scale-150" />
            <div className="relative bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-primary/10">
              <span className="material-symbols-outlined text-primary text-5xl">fact_check</span>
            </div>
          </div>
          
          {/* HeadlineText */}
          <h1 className="text-[#111817] dark:text-white tracking-tight text-3xl md:text-4xl font-bold leading-tight mb-4">
            📝 자격 확인을 시작합니다
          </h1>
          
          {/* BodyText */}
          <div className="space-y-4 mb-10">
            <p className="text-gray-600 dark:text-gray-400 text-lg leading-relaxed max-w-[520px] mx-auto">
              선택하신 정책의 요구사항에 맞춰 AI가 몇 가지 질문을 드릴 예정입니다.
              정확한 진단을 위해 기업 정보를 미리 준비해 주세요.
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-primary/5 dark:bg-primary/10 text-primary text-sm font-semibold rounded-full">
              <span className="material-symbols-outlined text-sm">schedule</span>
              약 2-3분 정도 소요됩니다
            </div>
          </div>
          
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{error}</p>
            </div>
          )}
          
          {/* ButtonGroup */}
          <div className="flex flex-col items-center gap-4 w-full max-w-[400px] mx-auto">
            <button
              onClick={handleStart}
              disabled={loading}
              className="flex items-center justify-center gap-2 w-full h-14 bg-primary hover:bg-opacity-90 text-white rounded-xl text-lg font-bold transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>처리중...</span>
                </>
              ) : (
                <>
                  <span>확인 시작</span>
                  <span className="material-symbols-outlined">arrow_forward</span>
                </>
              )}
            </button>
            <button
              onClick={() => router.back()}
              disabled={loading}
              className="flex items-center justify-center w-full h-14 bg-transparent text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-primary hover:bg-primary/5 rounded-xl text-base font-medium transition-all disabled:opacity-50"
            >
              취소하고 정책 상세로
            </button>
          </div>
          
          {/* Privacy/Data Notice */}
          <p className="mt-12 text-xs text-gray-400 dark:text-gray-500 flex items-center justify-center gap-1.5">
            <span className="material-symbols-outlined text-xs">lock</span>
            입력하신 정보는 자격 확인 용도로만 사용되며 안전하게 보호됩니다.
          </p>
        </div>
      </div>
      
      {/* Decorative Progress Steps (Inactive/Initial) */}
      <div className="mt-20 max-w-2xl mx-auto opacity-40">
        <div className="flex items-center justify-between relative">
          <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gray-200 dark:bg-gray-800 -translate-y-1/2 -z-10" />
          <div className="bg-primary size-4 rounded-full border-4 border-white dark:border-background-dark ring-4 ring-primary/20" />
          <div className="bg-gray-300 dark:bg-gray-700 size-3 rounded-full border-4 border-white dark:border-background-dark" />
          <div className="bg-gray-300 dark:bg-gray-700 size-3 rounded-full border-4 border-white dark:border-background-dark" />
          <div className="bg-gray-300 dark:bg-gray-700 size-3 rounded-full border-4 border-white dark:border-background-dark" />
        </div>
        <div className="flex justify-between mt-4 text-[10px] uppercase tracking-widest font-bold text-gray-400">
          <span>Introduction</span>
          <span>Basic Info</span>
          <span>Eligibility</span>
          <span>Result</span>
        </div>
      </div>
    </main>
  );
}

