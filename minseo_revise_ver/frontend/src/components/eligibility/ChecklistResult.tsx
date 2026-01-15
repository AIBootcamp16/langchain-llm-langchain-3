/**
 * ChecklistResult Component
 * 체크리스트 결과 컴포넌트
 */

'use client';

import React from 'react';
import { Badge } from '@/components/common/Badge';
import type { EligibilityResult } from '@/lib/types';

interface ChecklistResultProps {
  result: EligibilityResult;
}

export const ChecklistResult: React.FC<ChecklistResultProps> = ({ result }) => {
  const getResultBadge = () => {
    switch (result.result) {
      case 'ELIGIBLE':
        return <Badge variant="success" size="lg">✅ 자격 충족</Badge>;
      case 'NOT_ELIGIBLE':
        return <Badge variant="error" size="lg">❌ 자격 미충족</Badge>;
      case 'PARTIALLY':
        return <Badge variant="warning" size="lg">⚠️ 부분 충족</Badge>;
      default:
        return <Badge variant="default" size="lg">확인 필요</Badge>;
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Result Badge */}
      <div className="text-center mb-6">
        {getResultBadge()}
      </div>
      
      {/* Reason */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">종합 판정</h3>
        <p className="text-gray-700">{result.reason}</p>
      </div>
      
      {/* Details */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">상세 결과</h3>
        <div className="space-y-3">
          {result.details.map((detail, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg"
            >
              <div className="flex-shrink-0">
                {detail.status === 'PASS' && (
                  <span className="text-green-600 text-xl">✅</span>
                )}
                {detail.status === 'FAIL' && (
                  <span className="text-red-600 text-xl">❌</span>
                )}
                {detail.status === 'UNKNOWN' && (
                  <span className="text-gray-600 text-xl">❓</span>
                )}
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-1">
                  {detail.condition}
                </h4>
                <p className="text-sm text-gray-600">{detail.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

