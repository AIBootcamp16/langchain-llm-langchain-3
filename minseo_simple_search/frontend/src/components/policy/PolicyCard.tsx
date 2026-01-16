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
  // 상태 결정 로직 (실제로는 API에서 받아와야 함)
  const getStatus = () => {
    // 임시 로직
    const random = Math.random();
    if (random > 0.7) return { label: '모집예정', color: 'text-[#e03131] bg-[#fff5f5] border-[#ffc9c9]' };
    if (random > 0.3) return { label: '모집중', color: 'text-[#2b8a3e] bg-[#ebfbee] border-[#b2f2bb]' };
    return { label: '마감', color: 'text-gray-500 bg-gray-100 border-gray-300' };
  };
  
  const status = getStatus();
  
  return (
    <Link href={routes.policy(policy.id)}>
      <div className="group relative bg-white dark:bg-[#242828] rounded-xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-transparent hover:border-primary/20">
        <div className="flex flex-col md:flex-row">
          {/* Image placeholder */}
          <div className="w-full md:w-64 h-48 md:h-auto bg-gradient-to-br from-primary/20 to-primary/5 shrink-0 flex items-center justify-center">
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

