import React from 'react';
import { useRouter } from 'next/navigation';
import { Policy } from '@/lib/types';
import { routes } from '@/lib/routes';
import { Spinner } from '@/components/common/Spinner';

interface PolicyListProps {
  policies: Policy[];
  loading: boolean;
  emptyMessage?: string;
}

export function PolicyList({ policies, loading, emptyMessage = '정책이 없습니다.' }: PolicyListProps) {
  const router = useRouter();

  if (loading && policies.length === 0) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!loading && policies.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {policies.map((policy) => (
        <div
          key={policy.id}
          onClick={() => router.push(routes.policy(policy.id))}
          className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex gap-2 mb-2">
            {policy.region && (
              <span className="px-2 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded">
                {policy.region}
              </span>
            )}
            {policy.category && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-bold rounded">
                {policy.category}
              </span>
            )}
            {policy.source_type === 'web' && (
              <span className="px-2 py-1 bg-orange-50 text-orange-600 text-xs font-bold rounded">
                웹 검색
              </span>
            )}
          </div>
          
          <h3 className="text-lg font-bold mb-2 group-hover:text-[#27685d] transition-colors">
            {policy.program_name}
          </h3>
          
          <p className="text-gray-600 dark:text-gray-300 text-sm line-clamp-2 mb-4">
            {policy.program_overview || policy.support_description || '상세 정보 없음'}
          </p>
          
          <div className="flex justify-between items-center text-xs text-gray-500">
            {policy.supervising_ministry && <span>{policy.supervising_ministry}</span>}
            {policy.url && (
              <a 
                href={policy.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                출처 링크
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
