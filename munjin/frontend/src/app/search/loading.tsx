/**
 * Search Loading Page
 * 검색 중 로딩 화면
 */

import { Spinner } from '@/components/common/Spinner';

export default function SearchLoading() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-600 text-lg">정책을 검색하고 있습니다...</p>
      </div>
    </div>
  );
}

