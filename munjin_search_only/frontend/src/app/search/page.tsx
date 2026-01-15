/**
 * Search Page (화면 2, 3)
 * 정책 검색 결과 화면 - Stitch 디자인 적용
 *
 * 새로운 SimpleSearchService 기반 빠른 검색 사용
 * - LLM 호출 없이 빠른 벡터 검색
 * - 검색 품질 지표 및 근거 표시
 */

'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { PolicyList } from '@/components/policy/PolicyList';
import { searchPolicies, getRegions, getCategories } from '@/lib/api';
import { usePolicyStore } from '@/store/usePolicyStore';
import { routes } from '@/lib/routes';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get('query') || '';
  const regionParam = searchParams.get('region') || '';
  const categoryParam = searchParams.get('category') || '';

  const {
    policies,
    total,
    loading,
    summary,
    topScore,
    metrics,
    searchTimeMs,
    setSearchResult,
    setLoading,
    setError
  } = usePolicyStore();

  const [regions, setRegions] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState(regionParam);
  const [selectedCategory, setSelectedCategory] = useState(categoryParam);
  const [progress, setProgress] = useState(0);

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

  // Progress animation during loading (더 빠르게 - LLM 없음)
  useEffect(() => {
    if (loading) {
      setProgress(0);
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return 90;
          return prev + 15; // 더 빠른 진행
        });
      }, 100); // 더 짧은 간격
      return () => clearInterval(interval);
    } else {
      setProgress(100);
    }
  }, [loading]);

  // Load policies using new fast search API
  useEffect(() => {
    const loadPolicies = async () => {
      if (!query) return; // 쿼리가 없으면 검색하지 않음

      try {
        setLoading(true);
        // 새로운 빠른 검색 API 사용
        const data = await searchPolicies({
          query: query,
          region: selectedRegion || undefined,
          category: selectedCategory || undefined,
        });
        setSearchResult(data);
      } catch (error) {
        console.error('Failed to load policies:', error);
        setError('정책을 불러오는 데 실패했습니다.');
      }
    };

    loadPolicies();
  }, [query, selectedRegion, selectedCategory, setSearchResult, setLoading, setError]);

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
                빠른 벡터 검색으로 최적의 지원사업을 찾고 있습니다
              </p>
            </div>

            {/* Step-by-Step Checklist */}
            <div className="space-y-4 mb-10">
              {/* Step 1: Vector Search */}
              <div className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                progress > 30 ? 'bg-primary/5 border-primary/10' : 'border-[#d5e2e0] dark:border-gray-800'
              }`}>
                <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-primary text-white">
                  {progress > 30 ? (
                    <span className="material-symbols-outlined text-[16px]">check</span>
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
                  )}
                </div>
                <p className={`text-base ${progress > 30 ? 'font-semibold text-primary' : 'font-normal'}`}>
                  벡터 DB 검색 중
                </p>
              </div>

              {/* Step 2: Web Search (if needed) */}
              <div className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                progress > 60 ? 'border-primary/10 bg-primary/5' : 'border-[#d5e2e0] dark:border-gray-800'
              }`}>
                <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full border-2 border-primary/30 text-primary">
                  {progress > 60 ? (
                    <span className="material-symbols-outlined text-[16px]">check</span>
                  ) : progress > 30 ? (
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                  ) : null}
                </div>
                <p className={`text-base ${
                  progress > 60 ? 'font-semibold text-primary' : 'font-normal text-[#111817] dark:text-gray-300'
                }`}>
                  웹 검색 보충 확인 중
                </p>
              </div>

              {/* Step 3: Finalizing */}
              <div className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                progress > 80 ? 'border-[#d5e2e0] dark:border-gray-800' : 'border-transparent opacity-50'
              }`}>
                <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full border-2 border-gray-300 dark:border-gray-700">
                  {progress > 80 && <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>}
                </div>
                <p className="text-base font-normal text-gray-500">결과 정리 중</p>
              </div>
            </div>

            {/* Progress Bar Section */}
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-end">
                <span className="text-sm font-semibold text-primary/80">⚡ 빠른 검색 진행 중</span>
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
                &quot;LLM 호출 없이 빠르게 검색합니다&quot;
              </p>
            </div>
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
            Search Complete
          </span>
          {query && (
            <span className="text-sm text-text-muted">
              &quot;{query}&quot; 검색 결과
            </span>
          )}
          {searchTimeMs > 0 && (
            <span className="text-xs text-gray-400">
              ({searchTimeMs}ms)
            </span>
          )}
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
          ✅ 관련 정책 {total}건을 찾았어요
        </h1>
        {summary ? (
          <p className="text-text-muted dark:text-text-muted-light max-w-2xl leading-relaxed">
            {summary}
          </p>
        ) : (
          <p className="text-text-muted dark:text-text-muted-light max-w-2xl leading-relaxed">
            검색 결과를 확인하세요.
          </p>
        )}

        {/* 검색 품질 지표 표시 */}
        {metrics && (
          <div className="mt-4 flex flex-wrap gap-2">
            {topScore > 0 && (
              <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                최고 유사도: {(topScore * 100).toFixed(0)}%
              </span>
            )}
            {metrics.avg_score > 0 && (
              <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                평균 유사도: {(metrics.avg_score * 100).toFixed(0)}%
              </span>
            )}
            {metrics.web_search_triggered && (
              <span className="px-2 py-1 text-xs rounded bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300">
                웹 검색 포함 ({metrics.web_search_count}건)
              </span>
            )}
            <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
              임계값: {(metrics.score_threshold_used * 100).toFixed(0)}%
            </span>
          </div>
        )}
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
          Fast Vector Search • 2024
        </p>
      </div>
    </main>
  );
}
