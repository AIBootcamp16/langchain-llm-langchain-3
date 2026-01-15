/**
 * Search Page (화면 2, 3)
 * 정책 검색 결과 화면 - Stitch 디자인 적용
 */

'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { PolicyList } from '@/components/policy/PolicyList';
import { getPolicies, getRegions, getCategories } from '@/lib/api';
import { usePolicyStore } from '@/store/usePolicyStore';
import { routes } from '@/lib/routes';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get('query') || '';
  const regionParam = searchParams.get('region') || '';
  const categoryParam = searchParams.get('category') || '';
  
  const { policies, total, loading, setPolicies, setLoading, setError } = usePolicyStore();
  
  const [regions, setRegions] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState(regionParam);
  const [selectedCategory, setSelectedCategory] = useState(categoryParam);
  
  // 필터 변경 시 페이지 1로 리셋
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedRegion, selectedCategory, query]);
  const [progress, setProgress] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 7; // 페이지당 7개
  
  // Load filters
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [regionsData, categoriesData] = await Promise.all([
          getRegions(),
          getCategories(),
        ]);
        setRegions(regionsData);
        setCategories(categoriesData);
      } catch (error) {
        console.error('Failed to load filters:', error);
      }
    };
    
    loadFilters();
  }, []);
  
  // Progress animation during loading
  useEffect(() => {
    if (loading) {
      setProgress(0);
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return 90;
          return prev + 10;
        });
      }, 200);
      return () => clearInterval(interval);
    } else {
      setProgress(100);
    }
  }, [loading]);
  
  // Load policies
  useEffect(() => {
    const loadPolicies = async () => {
      try {
        setLoading(true);
        // page를 offset으로 변환: offset = (page - 1) * limit
        const offset = (currentPage - 1) * pageSize;
        const data = await getPolicies({
          query: query || undefined,
          region: selectedRegion || undefined,
          category: selectedCategory || undefined,
          limit: pageSize,
          offset: offset,
        });
        setPolicies(data);
      } catch (error) {
        console.error('Failed to load policies:', error);
        setError('정책을 불러오는 데 실패했습니다.');
      }
    };
    
    loadPolicies();
  }, [query, selectedRegion, selectedCategory, currentPage, setPolicies, setLoading, setError]);
  
  // Show loading screen
  if (loading && policies.length === 0) {
    return (
      <main className="flex-1 flex items-center justify-center p-6 relative overflow-hidden">
        {/* Background Decorative Elements */}
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <div className="absolute top-[-10%] left-[-5%] w-1/2 h-1/2 rounded-full bg-primary/20 blur-[100px]"></div>
          <div className="absolute bottom-[-10%] right-[-5%] w-1/2 h-1/2 rounded-full bg-primary/30 blur-[120px]"></div>
        </div>

        <div className="flex flex-col max-w-[640px] w-full z-10">
          {/* Status Card */}
          <div className="bg-white dark:bg-gray-900/50 backdrop-blur-sm border border-[#eaf0ef] dark:border-gray-800 rounded-xl shadow-xl p-8 md:p-12">
            {/* Icon Area */}
            <div className="flex justify-center mb-8">
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 rounded-full scale-150 blur-xl"></div>
                <div className="relative bg-primary text-white p-4 rounded-xl shadow-lg">
                  <span className="material-symbols-outlined text-4xl">search_spark</span>
                </div>
              </div>
            </div>

            {/* Headline */}
            <div className="text-center mb-10">
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-2">
                🔍 관련 정책을 찾고 있어요
              </h1>
              <p className="text-[#5e8781] dark:text-gray-400 font-medium">
                스타트업과 소상공인을 위한 최적의 지원사업을 분석 중입니다
              </p>
            </div>

            {/* Step-by-Step Checklist */}
            <div className="space-y-4 mb-10">
              {/* Step 1: Completed */}
              <div className="flex items-center gap-4 p-4 rounded-lg bg-primary/5 border border-primary/10 transition-all">
                <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-primary text-white">
                  <span className="material-symbols-outlined text-[16px]">check</span>
                </div>
                <p className="text-base font-semibold text-primary">내부 정책 DB 검색 중</p>
              </div>

              {/* Step 2: In Progress */}
              <div className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                progress > 50 ? 'border-primary/10 bg-primary/5' : 'border-[#d5e2e0] dark:border-gray-800'
              }`}>
                <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full border-2 border-primary/30 text-primary">
                  {progress > 50 ? (
                    <span className="material-symbols-outlined text-[16px]">check</span>
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                  )}
                </div>
                <p className={`text-base ${
                  progress > 50 ? 'font-semibold text-primary' : 'font-normal text-[#111817] dark:text-gray-300'
                }`}>
                  최신 공고 웹 검색 확인 중
                </p>
              </div>

              {/* Step 3: Pending */}
              <div className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                progress > 80 ? 'border-[#d5e2e0] dark:border-gray-800' : 'border-transparent opacity-50'
              }`}>
                <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full border-2 border-gray-300 dark:border-gray-700">
                  {progress > 80 && <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>}
                </div>
                <p className="text-base font-normal text-gray-500">맞춤형 보조금 리스트 생성</p>
              </div>
            </div>

            {/* Progress Bar Section */}
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-end">
                <span className="text-sm font-semibold text-primary/80">⏳ 잠시만 기다려 주세요</span>
                <span className="text-2xl font-bold text-primary tracking-tighter">{progress}%</span>
              </div>
              <div className="h-3 w-full rounded-full bg-[#d5e2e0] dark:bg-gray-800 overflow-hidden relative">
                <div 
                  className="h-full rounded-full bg-primary transition-all duration-300 ease-out relative"
                  style={{ width: `${progress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                </div>
              </div>
              <p className="text-[#5e8781] dark:text-gray-500 text-sm leading-relaxed text-center mt-2 italic">
                &quot;AI가 사업자 등록 정보를 바탕으로 최적의 보조금을 분석하고 있습니다.&quot;
              </p>
            </div>
          </div>

          {/* Fun Fact */}
          <div className="mt-8 px-4 flex items-start gap-4 text-sm text-gray-500 dark:text-gray-400">
            <span className="material-symbols-outlined text-primary/60">info</span>
            <p>알고 계셨나요? 정부 지원 사업의 약 40%는 매달 초에 집중적으로 공고됩니다.</p>
          </div>
        </div>

        <style jsx>{`
          @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }
          .animate-shimmer {
            animation: shimmer 2s infinite linear;
          }
        `}</style>
      </main>
    );
  }
  
  return (
    <main className="max-w-[1000px] mx-auto px-6 py-12">
      {/* Result Heading */}
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-2.5 py-1 rounded bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
            Analysis Complete
          </span>
          {query && (
            <span className="text-sm text-text-muted">
              &quot;{query}&quot; 검색 결과
            </span>
          )}
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
          ✅ 관련 정책 {total}건을 찾았어요
        </h1>
        <p className="text-text-muted dark:text-text-muted-light max-w-2xl leading-relaxed">
          AI가 귀하의 상황에 가장 적합한 정책들을 선별했습니다. 아래에서 상세 내용을 확인하세요.
        </p>
      </div>
      
      {/* Filters */}
      {(regions.length > 0 || categories.length > 0) && (
        <div className="mb-6 flex flex-wrap gap-3">
          {regions.length > 0 && (
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">전체 지역</option>
              {regions.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
          )}
          
          {categories.length > 0 && (
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">전체 카테고리</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          )}
        </div>
      )}
      
      {/* Results */}
      <PolicyList
        policies={policies}
        loading={loading}
        emptyMessage="검색 결과가 없습니다. 다른 조건으로 검색해보세요."
      />
      
      {/* Pagination */}
      {total > pageSize && (
        <div className="mt-12 flex items-center justify-center gap-2">
          {/* Previous Button */}
          <button
            onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-all flex items-center gap-1"
          >
            <span className="material-symbols-outlined text-[20px]">chevron_left</span>
            이전
          </button>
          
          {/* Page Numbers */}
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.ceil(total / pageSize) }, (_, i) => i + 1)
              .filter((page) => {
                // 현재 페이지 주변 5개만 표시
                const diff = Math.abs(page - currentPage);
                return diff === 0 || diff <= 2 || page === 1 || page === Math.ceil(total / pageSize);
              })
              .map((page, index, array) => {
                // "..." 표시를 위한 로직
                const prevPage = array[index - 1];
                const showEllipsis = prevPage && page - prevPage > 1;
                
                return (
                  <React.Fragment key={page}>
                    {showEllipsis && (
                      <span className="px-3 py-2 text-gray-400">...</span>
                    )}
                    <button
                      onClick={() => setCurrentPage(page)}
                      className={`min-w-[40px] h-[40px] rounded-lg font-bold transition-all ${
                        currentPage === page
                          ? 'bg-primary text-white shadow-lg'
                          : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      {page}
                    </button>
                  </React.Fragment>
                );
              })}
          </div>
          
          {/* Next Button */}
          <button
            onClick={() => setCurrentPage((prev) => Math.min(Math.ceil(total / pageSize), prev + 1))}
            disabled={currentPage === Math.ceil(total / pageSize)}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-all flex items-center gap-1"
          >
            다음
            <span className="material-symbols-outlined text-[20px]">chevron_right</span>
          </button>
        </div>
      )}
      
      {/* Back Button Footer */}
      <div className="mt-16 flex flex-col items-center border-t border-[#eaf0ef] dark:border-[#2d3332] pt-12">
        <button
          onClick={() => router.push(routes.home)}
          className="group flex items-center gap-3 px-8 py-3 rounded-full bg-[#eaf0ef] dark:bg-[#2d3332] text-[#111817] dark:text-[#eaf0ef] font-bold text-sm hover:bg-primary hover:text-white transition-all"
        >
          <span className="material-symbols-outlined group-hover:-translate-x-1 transition-transform">arrow_back</span>
          Home으로 돌아가기
        </button>
        <p className="mt-8 text-xs text-text-muted uppercase tracking-[0.2em] font-medium">
          AI Powered Search Result • 2024
        </p>
      </div>
    </main>
  );
}

