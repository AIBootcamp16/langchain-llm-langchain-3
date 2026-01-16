/**
 * Eligibility Result Page (화면 7)
 * 자격 확인 결과 화면 - Stitch 디자인 적용
 */

'use client';

import React, { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Spinner } from '@/components/common/Spinner';
import { getEligibilityResult } from '@/lib/api';
import { useEligibilityStore } from '@/store/useEligibilityStore';
import { routes } from '@/lib/routes';

export default function EligibilityResultPage() {
  const params = useParams();
  const router = useRouter();
  const policyId = Number(params.policyId);
  
  const { sessionId, result, setResult, setLoading, loading, reset } = useEligibilityStore();
  
  useEffect(() => {
    const loadResult = async () => {
      if (!sessionId) {
        router.push(routes.eligibilityStart(policyId));
        return;
      }
      
      if (result) return;
      
      try {
        setLoading(true);
        const data = await getEligibilityResult(sessionId);
        setResult(data);
      } catch (error) {
        console.error('Failed to load result:', error);
        router.push(routes.eligibilityStart(policyId));
      } finally {
        setLoading(false);
      }
    };
    
    loadResult();
  }, [sessionId, result, policyId, router, setResult, setLoading]);
  
  if (loading || !result) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center min-h-[60vh]">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }
  
  const isEligible = result.eligible;
  
  return (
    <main className="max-w-[800px] mx-auto px-6 py-12">
      {/* Page Heading */}
      <div className="mb-10 text-center">
        <h1 className="text-3xl md:text-4xl font-black leading-tight tracking-tight mb-4">
          ✅ 자격 체크리스트 결과
        </h1>
        <p className="text-text-muted dark:text-text-muted-light text-lg font-normal">
          입력하신 정보를 바탕으로 해당 정책의 적합도를 분석했습니다.
        </p>
      </div>
      
      {/* Result Status Card */}
      <div className="bg-white dark:bg-[#252a2e] rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none border border-[#eaf0ef] dark:border-[#333] overflow-hidden mb-8">
        <div className="p-8 border-b border-[#eaf0ef] dark:border-[#333] bg-primary/5">
          <div className="flex items-center gap-4">
            <div className="bg-primary/10 p-3 rounded-xl">
              <span className="material-symbols-outlined text-primary text-3xl">description</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-primary/70 uppercase tracking-wider">Target Policy</p>
              <h3 className="text-xl font-bold">정책 자격 확인 결과</h3>
            </div>
          </div>
        </div>
        <div className="p-8">
          <h4 className="text-sm font-bold text-text-muted dark:text-text-muted-light mb-6 uppercase tracking-widest">
            분석 리포트
          </h4>
          <div className="space-y-4">
            {result.requirements && result.requirements.map((req, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between p-4 rounded-xl border ${
                  req.met
                    ? 'border-[#eaf0ef] dark:border-[#333] hover:bg-background-light dark:hover:bg-[#2c3236]'
                    : 'border-[#DB924B]/30 bg-[#DB924B]/5 hover:bg-[#DB924B]/10'
                } transition-colors`}
              >
                <div className="flex items-center gap-4">
                  <div
                    className={`flex items-center justify-center rounded-full shrink-0 size-10 ${
                      req.met
                        ? 'text-[#078830] bg-[#078830]/10'
                        : 'text-[#DB924B] bg-[#DB924B]/20'
                    }`}
                  >
                    <span className="material-symbols-outlined">
                      {req.met ? 'check_circle' : 'cancel'}
                    </span>
                  </div>
                  <p className="text-lg font-medium">{req.requirement}</p>
                </div>
                <div
                  className={`shrink-0 flex items-center gap-2 px-3 py-1 rounded-full border ${
                    req.met
                      ? 'text-[#078830] bg-[#078830]/5 border-[#078830]/20'
                      : 'text-[#DB924B] bg-[#DB924B]/5 border-[#DB924B]/20'
                  }`}
                >
                  <span className="text-sm font-bold">{req.met ? '충족' : '미충족'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Warning/Success Message Banner */}
      {!isEligible ? (
        <div className="bg-[#DB924B]/10 border-2 border-dashed border-[#DB924B]/30 rounded-xl p-6 flex items-start gap-4 mb-10">
          <span className="material-symbols-outlined text-[#DB924B] text-3xl">warning</span>
          <div className="space-y-1">
            <p className="text-[#DB924B] text-xl font-black">⚠️ 해당 정책 신청은 어려워요</p>
            <p className="text-[#DB924B]/80 text-base">
              일부 자격 조건이 충족되지 않아 본 사업의 신청 자격에서 제외되었습니다. 
              다시 확인하시거나 다른 지원 사업을 탐색해보세요.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-[#078830]/10 border-2 border-dashed border-[#078830]/30 rounded-xl p-6 flex items-start gap-4 mb-10">
          <span className="material-symbols-outlined text-[#078830] text-3xl">check_circle</span>
          <div className="space-y-1">
            <p className="text-[#078830] text-xl font-black">✅ 해당 정책에 신청 가능합니다!</p>
            <p className="text-[#078830]/80 text-base">
              모든 자격 조건을 충족하였습니다. 정책 상세 페이지에서 신청 방법을 확인하세요.
            </p>
          </div>
        </div>
      )}
      
      {/* Buttons Section */}
      <div className="flex flex-col md:flex-row items-center gap-4">
        <button
          onClick={() => router.push(routes.policy(policyId))}
          className="w-full md:flex-1 bg-primary text-white h-14 rounded-xl font-bold text-lg hover:bg-primary/90 transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
        >
          <span className="material-symbols-outlined">article</span>
          정책 상세로 돌아가기
        </button>
        <button
          onClick={() => {
            reset();
            router.push(routes.eligibilityStart(policyId));
          }}
          className="w-full md:flex-1 bg-white dark:bg-[#252a2e] border border-[#eaf0ef] dark:border-[#333] text-[#111817] dark:text-white h-14 rounded-xl font-bold text-lg hover:bg-background-light dark:hover:bg-[#2c3236] transition-all flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined">refresh</span>
          다시 확인하기
        </button>
      </div>
      
      <div className="mt-4 flex justify-center">
        <button
          onClick={() => router.push(routes.search)}
          className="text-text-muted hover:text-primary text-sm font-semibold flex items-center gap-1 transition-colors"
        >
          <span className="material-symbols-outlined text-[18px]">search</span>
          다른 정책 찾아보기
        </button>
      </div>
      
      {/* Footer Help */}
      <div className="mt-12 text-center p-6 bg-primary/5 rounded-2xl border border-primary/10">
        <p className="text-primary font-medium mb-2">도움이 필요하신가요?</p>
        <p className="text-sm text-text-muted">
          AI 어시스턴트에게 물어보면 현재 상황에 맞는 최적의 정책을 추천해드립니다.
        </p>
        <button
          onClick={() => router.push(routes.policyQA(policyId))}
          className="mt-4 text-primary font-bold text-sm underline hover:no-underline"
        >
          AI와 상담 시작하기 →
        </button>
      </div>
    </main>
  );
}

