/**
 * PolicySummary Component
 * 정책 요약 정보 컴포넌트
 */

'use client';

import React from 'react';
import { Badge } from '@/components/common/Badge';
import type { Policy } from '@/lib/types';

interface PolicySummaryProps {
  policy: Policy;
}

export const PolicySummary: React.FC<PolicySummaryProps> = ({ policy }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Title */}
      <h1 className="text-3xl font-bold text-gray-900 mb-4">
        {policy.program_name}
      </h1>
      
      {/* Badges */}
      <div className="flex gap-2 mb-6">
        <Badge variant="info">{policy.region}</Badge>
        <Badge variant="default">{policy.category}</Badge>
      </div>
      
      {/* Description */}
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">지원 내용</h3>
          <p className="text-gray-600">{policy.support_description}</p>
        </div>
        
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">신청 대상</h3>
          <p className="text-gray-600">{policy.apply_target}</p>
        </div>
        
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">지원 상세</h3>
          <p className="text-gray-600">{policy.support_details}</p>
        </div>
        
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">신청 방법</h3>
          <p className="text-gray-600">{policy.apply_method}</p>
        </div>
        
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">문의처</h3>
          <p className="text-gray-600">{policy.contact}</p>
        </div>
        
        {policy.url && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">상세 URL</h3>
            <a
              href={policy.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              {policy.url}
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

