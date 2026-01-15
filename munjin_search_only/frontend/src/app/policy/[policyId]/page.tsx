/**
 * Policy Detail Page (화면 4)
 * 정책 상세 화면 - Stitch 디자인 적용
 */

'use client';

import React, { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Spinner } from '@/components/common/Spinner';
import { getPolicy } from '@/lib/api';
import { usePolicyStore } from '@/store/usePolicyStore';
import { routes } from '@/lib/routes';

export default function PolicyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const policyId = Number(params.policyId);
  
  const { currentPolicy, loading, setCurrentPolicy, setLoading, setError } = usePolicyStore();
  
  useEffect(() => {
    const loadPolicy = async () => {
      try {
        setLoading(true);
        const policy = await getPolicy(policyId);
        setCurrentPolicy(policy);
      } catch (error) {
        console.error('Failed to load policy:', error);
        setError('정책을 불러오는 데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    loadPolicy();
  }, [policyId, setCurrentPolicy, setLoading, setError]);
  
  if (loading || !currentPolicy) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center min-h-[60vh]">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }
  
  return (
    <main className="flex-1 w-full max-w-[1200px] mx-auto px-6 py-8">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 mb-6 text-sm">
        <a className="text-text-muted hover:underline cursor-pointer" onClick={() => router.push(routes.search)}>
          All Policies
        </a>
        <span className="material-symbols-outlined text-xs text-text-muted">chevron_right</span>
        <span className="text-[#111817] dark:text-white font-semibold">Policy Details</span>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Content: Policy Details */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {/* PageHeading */}
          <div className="bg-white dark:bg-gray-900 rounded-xl p-8 border border-[#eaf0ef] dark:border-gray-800 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-16 -mt-16" />
            <div className="flex flex-col gap-4 relative z-10">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 bg-primary/10 text-primary text-xs font-bold rounded-full uppercase tracking-wider">
                  Active Policy
                </span>
                <span className="text-text-muted text-sm font-medium">
                  {currentPolicy.region} • {currentPolicy.category}
                </span>
              </div>
              <h1 className="text-[#111817] dark:text-white text-4xl font-extrabold leading-tight tracking-tight">
                {currentPolicy.program_name}
              </h1>
              <p className="text-text-muted text-lg max-w-2xl leading-relaxed">
                {currentPolicy.support_description}
              </p>
              <div className="flex flex-wrap gap-3 mt-2">
                <button className="flex items-center gap-2 px-4 py-2 bg-[#eaf0ef] dark:bg-gray-800 text-[#111817] dark:text-white text-sm font-bold rounded-lg hover:bg-[#d9e4e2] transition-colors">
                  <span className="material-symbols-outlined text-lg">share</span>
                  Share Policy
                </button>
                <button className="flex items-center gap-2 px-4 py-2 border border-[#eaf0ef] dark:border-gray-800 text-text-muted text-sm font-bold rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <span className="material-symbols-outlined text-lg">bookmark</span>
                  Save to Favorites
                </button>
              </div>
            </div>
          </div>
          
          {/* Eligibility Card */}
          <div className="bg-white dark:bg-gray-900 rounded-xl overflow-hidden border border-[#eaf0ef] dark:border-gray-800 shadow-sm">
            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary">groups</span>
                <h3 className="text-[#111817] dark:text-white text-xl font-bold">[지원 대상] Eligibility</h3>
              </div>
              <div className="space-y-4">
                <p className="text-[#111817] dark:text-gray-300 font-semibold text-base">
                  {currentPolicy.apply_target}
                </p>
              </div>
            </div>
          </div>
          
          {/* Benefits Card */}
          <div className="bg-white dark:bg-gray-900 rounded-xl overflow-hidden border border-[#eaf0ef] dark:border-gray-800 shadow-sm">
            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary">redeem</span>
                <h3 className="text-[#111817] dark:text-white text-xl font-bold">[지원 내용] Benefits</h3>
              </div>
              <div className="space-y-4">
                <p className="text-[#111817] dark:text-gray-300 text-base">
                  {currentPolicy.support_details || currentPolicy.support_description || '지원 내용 정보가 없습니다.'}
                </p>
                {currentPolicy.support_budget && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm font-semibold text-text-muted mb-2">지원 예산:</p>
                    <p className="text-sm text-text-muted">{currentPolicy.support_budget.toLocaleString()}원</p>
                  </div>
                )}
                {(currentPolicy.apply_method || currentPolicy.application_method) && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm font-semibold text-text-muted mb-2">신청 방법:</p>
                    <p className="text-sm text-text-muted">{currentPolicy.apply_method || currentPolicy.application_method}</p>
                  </div>
                )}
                {(currentPolicy.contact || currentPolicy.contact_agency) && (
                  <div className="pt-2">
                    <p className="text-sm font-semibold text-text-muted mb-1">문의처:</p>
                    <p className="text-sm text-text-muted">{currentPolicy.contact || currentPolicy.contact_agency}</p>
                    {currentPolicy.contact_number && currentPolicy.contact_number.length > 0 && (
                      <p className="text-sm text-text-muted mt-1">
                        {currentPolicy.contact_number.join(', ')}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Right Sidebar: Quick Actions */}
        <aside className="lg:col-span-4 sticky top-24 space-y-6">
          {/* Action Hub */}
          <div className="bg-[#27685d]/5 dark:bg-primary/10 rounded-xl p-6 border border-primary/20">
            <h4 className="text-primary dark:text-primary text-sm font-bold uppercase tracking-widest mb-4">
              Smart Actions
            </h4>
            <div className="flex flex-col gap-4">
              <button
                onClick={() => router.push(routes.policyQA(policyId))}
                className="group relative flex flex-col items-start gap-1 w-full bg-primary hover:bg-[#1a4a41] text-white p-5 rounded-xl transition-all shadow-lg shadow-primary/20"
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-lg font-extrabold">자세히 물어보기 ▶</span>
                  <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">smart_toy</span>
                </div>
                <p className="text-white/80 text-xs font-medium">Ask AI about specific details</p>
              </button>
              <button
                onClick={() => router.push(routes.eligibilityStart(policyId))}
                className="group relative flex flex-col items-start gap-1 w-full bg-white dark:bg-gray-800 border-2 border-primary text-primary dark:text-white p-5 rounded-xl transition-all hover:bg-primary/5"
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-lg font-extrabold">내가 해당되는지 확인 ▶</span>
                  <span className="material-symbols-outlined group-hover:scale-110 transition-transform">fact_check</span>
                </div>
                <p className="text-text-muted dark:text-gray-400 text-xs font-medium">Start eligibility checklist</p>
              </button>
            </div>
          </div>
          
          {/* Resources */}
          {currentPolicy.url && (
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-[#eaf0ef] dark:border-gray-800 shadow-sm">
              <h4 className="text-[#111817] dark:text-white text-sm font-bold mb-4">Official Resources</h4>
              <div className="flex flex-col gap-3">
                <a
                  href={currentPolicy.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-[#eaf0ef] transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">link</span>
                    <span className="text-sm font-medium">Application Portal</span>
                  </div>
                  <span className="material-symbols-outlined text-sm opacity-0 group-hover:opacity-100 transition-opacity">open_in_new</span>
                </a>
              </div>
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}

