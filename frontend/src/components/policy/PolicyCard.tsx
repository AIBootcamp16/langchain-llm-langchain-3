/**
 * PolicyCard Component
 * 정책 카드 컴포넌트 - Stitch 디자인 적용
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { routes } from '@/lib/routes';
import type { Policy } from '@/lib/types';

interface PolicyCardProps {
  policy: Policy;
}

export const PolicyCard: React.FC<PolicyCardProps> = ({ policy }) => {
  // 웹 검색 결과 여부 확인
  const isWebResult = policy.region === '웹 검색' || policy.id < 0;
  
  // 상태 결정 로직 (실제로는 API에서 받아와야 함)
  const getStatus = () => {
    // 임시 로직
    const random = Math.random();
    if (random > 0.7) return { label: '모집예정', color: 'text-[#e03131] bg-[#fff5f5] border-[#ffc9c9]' };
    if (random > 0.3) return { label: '모집중', color: 'text-[#2b8a3e] bg-[#ebfbee] border-[#b2f2bb]' };
    return { label: '마감', color: 'text-gray-500 bg-gray-100 border-gray-300' };
  };
  
  const status = getStatus();
  
  // 웹 검색 결과인 경우 웹 상세 페이지로 이동
  const getLinkHref = () => {
    if (isWebResult) {
      // 웹 검색 결과 → 웹 상세 페이지
      const webId = `web_${Math.abs(policy.id)}`;
      const title = encodeURIComponent(policy.program_name);
      const url = encodeURIComponent(policy.support_description.replace('출처: ', ''));
      const content = encodeURIComponent(policy.program_overview || '');
      const screenshotUrl = (policy as any).screenshot_url || '';
      const faviconUrl = (policy as any).favicon_url || '';
      
      console.log('=== PolicyCard 웹 검색 결과 ===');
      console.log('policy:', policy);
      console.log('screenshotUrl:', screenshotUrl);
      console.log('faviconUrl:', faviconUrl);
      
      return `/policy/web-detail/${webId}?title=${title}&url=${url}&content=${content}&screenshot=${encodeURIComponent(screenshotUrl)}&favicon=${encodeURIComponent(faviconUrl)}`;
    } else {
      // DB 정책
      return routes.policy(policy.id);
    }
  };
  
  // 웹 검색 결과는 카드 형태는 다르지만 Link로 감싸기
  if (isWebResult) {
    return (
      <Link href={getLinkHref()}>
        <div className="group relative bg-white dark:bg-[#242828] rounded-xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-transparent hover:border-primary/20">
        <div className="flex flex-col md:flex-row">
          {/* Image placeholder or Screenshot */}
          <div className="relative w-full md:w-64 h-48 md:h-auto bg-gradient-to-br from-primary/20 to-primary/5 shrink-0 flex items-center justify-center overflow-hidden">
            {isWebResult && (policy as any).screenshot_url ? (
              <>
                <img 
                  src={(policy as any).screenshot_url}
                  alt={policy.program_name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    // 스크린샷 로드 실패 시 기본 아이콘 표시
                    e.currentTarget.style.display = 'none';
                  }}
                />
                {/* 웹 검색 배지 */}
                <div className="absolute top-3 right-3 bg-white/90 dark:bg-gray-800/90 px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-md">
                  <span className="material-symbols-outlined text-[16px]">language</span>
                  <span>웹 검색</span>
                </div>
                {/* 기본 아이콘 (폴백) */}
                <span className="material-symbols-outlined text-primary text-5xl opacity-30 absolute">policy</span>
              </>
            ) : (
              <span className="material-symbols-outlined text-primary text-5xl opacity-30">policy</span>
            )}
          </div>
          
          <div className="flex-1 p-6 md:p-8 flex flex-col justify-between">
            <div>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-3 py-1 bg-[#eaf0ef] dark:bg-[#2d3332] text-[#111817] dark:text-[#eaf0ef] text-xs font-bold rounded">
                  {policy.region}
                </span>
                <span className="px-3 py-1 bg-[#eaf0ef] dark:bg-[#2d3332] text-[#111817] dark:text-[#eaf0ef] text-xs font-bold rounded">
                  {policy.category}
                </span>
                <span className={`px-3 py-1 text-xs font-bold rounded border ${status.color}`}>
                  {status.label}
                </span>
              </div>
              <div className="flex items-start gap-3 mb-3">
                {isWebResult && (policy as any).favicon_url && (
                  <img 
                    src={(policy as any).favicon_url}
                    alt="favicon"
                    className="w-8 h-8 rounded mt-1 shrink-0"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                )}
                <h3 className="text-xl font-bold group-hover:text-primary transition-colors">
                  {policy.program_name}
                </h3>
              </div>
              <p className="text-sm text-text-muted dark:text-text-muted-light mb-6 line-clamp-2">
                {policy.support_description || policy.apply_target}
              </p>
            </div>
            <div className="flex items-center justify-between mt-auto">
              <div className="flex items-center gap-4">
                <span className="text-xs text-text-muted">자세히 보기</span>
              </div>
              <button className="bg-primary hover:bg-[#1f534a] text-white px-6 py-2.5 rounded-lg font-bold text-sm flex items-center gap-2 transition-all">
                자세히 보기
                <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      </Link>
    );
  }
  
  // 일반 정책 카드
  return (
    <Link href={routes.policy(policy.id)}>
      <div className="group relative bg-white dark:bg-[#242828] rounded-xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-transparent hover:border-primary/20">
        <div className="flex flex-col md:flex-row">
          {/* Image placeholder */}
          <div className="relative w-full md:w-64 h-48 md:h-auto bg-gradient-to-br from-primary/20 to-primary/5 shrink-0 flex items-center justify-center overflow-hidden">
            <span className="material-symbols-outlined text-primary text-5xl opacity-30">policy</span>
          </div>
          
          <div className="flex-1 p-6 md:p-8 flex flex-col justify-between">
            <div>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-3 py-1 bg-[#eaf0ef] dark:bg-[#2d3332] text-[#111817] dark:text-[#eaf0ef] text-xs font-bold rounded">
                  {policy.region}
                </span>
                <span className="px-3 py-1 bg-[#eaf0ef] dark:bg-[#2d3332] text-[#111817] dark:text-[#eaf0ef] text-xs font-bold rounded">
                  {policy.category}
                </span>
                <span className={`px-3 py-1 text-xs font-bold rounded border ${status.color}`}>
                  {status.label}
                </span>
              </div>
              <h3 className="text-xl font-bold mb-3 group-hover:text-primary transition-colors">
                {policy.program_name}
              </h3>
              <p className="text-sm text-text-muted dark:text-text-muted-light mb-6 line-clamp-2">
                {policy.support_description || policy.apply_target}
              </p>
            </div>
            <div className="flex items-center justify-between mt-auto">
              <div className="flex items-center gap-4">
                <span className="text-xs text-text-muted">자세히 보기</span>
              </div>
              <button className="bg-primary hover:bg-[#1f534a] text-white px-6 py-2.5 rounded-lg font-bold text-sm flex items-center gap-2 transition-all">
                자세히 보기
                <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
};

