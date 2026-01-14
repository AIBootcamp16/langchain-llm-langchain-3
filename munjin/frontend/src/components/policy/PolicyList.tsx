/**
 * PolicyList Component
 * 정책 목록 컴포넌트 - Stitch 디자인 적용
 */

'use client';

import React from 'react';
import { PolicyCard } from './PolicyCard';
import { Spinner } from '@/components/common/Spinner';
import type { Policy } from '@/lib/types';

interface PolicyListProps {
  policies: Policy[];
  loading?: boolean;
  emptyMessage?: string;
}

export const PolicyList: React.FC<PolicyListProps> = ({
  policies,
  loading = false,
  emptyMessage = '검색 결과가 없습니다.',
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }
  
  if (!policies || policies.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted dark:text-text-muted-light text-lg">{emptyMessage}</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {policies.map((policy) => (
        <PolicyCard key={policy.id} policy={policy} />
      ))}
    </div>
  );
};

