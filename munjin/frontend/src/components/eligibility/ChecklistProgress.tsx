/**
 * ChecklistProgress Component
 * 체크리스트 진행률 컴포넌트
 */

'use client';

import React from 'react';

interface ChecklistProgressProps {
  current: number;
  total: number;
}

export const ChecklistProgress: React.FC<ChecklistProgressProps> = ({ current, total }) => {
  const percentage = total > 0 ? (current / total) * 100 : 0;
  
  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">
          진행률: {current} / {total}
        </span>
        <span className="text-sm font-medium text-primary-600">
          {Math.round(percentage)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="bg-primary-600 h-3 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

