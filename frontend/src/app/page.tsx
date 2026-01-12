/**
 * Home Page (화면 1)
 * 메인 홈 화면 - Stitch 디자인 적용
 */

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { routes } from '@/lib/routes';

export default function HomePage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`${routes.search}?query=${encodeURIComponent(searchQuery)}`);
    } else {
      router.push(routes.search);
    }
  };

  const quickKeywords = ['창업', '소상공인', '프리랜서'];
  const regions = ['서울', '경기', '부산', '전국'];
  
  return (
    <main className="flex-1 flex flex-col items-center justify-center px-6 pb-32">
      <div className="w-full max-w-3xl flex flex-col items-center">
        <div className="mb-10 text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
            복잡한 정책과 지원금,<br />
            <span className="text-primary">무엇이든 물어보세요</span>
          </h1>
          <p className="text-text-muted dark:text-text-muted-light text-lg">
            AI가 당신의 비즈니스에 꼭 맞는 혜택을 찾아드립니다.
          </p>
        </div>
        
        {/* Search Form */}
        <form onSubmit={handleSearch} className="w-full relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 to-primary/10 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
          <div className="relative flex flex-col md:flex-row w-full bg-white dark:bg-gray-900 rounded-xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-800">
            <div className="flex items-center pl-6 text-gray-400">
              <span className="material-symbols-outlined text-2xl">search</span>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 h-16 border-none focus:ring-0 text-lg px-4 bg-transparent placeholder:text-gray-400 text-gray-800 dark:text-white outline-none"
              placeholder="예비창업자 지원금 알려줘"
            />
            <div className="p-2">
              <button
                type="submit"
                className="h-12 px-8 bg-primary text-white rounded-lg font-bold flex items-center gap-2 hover:bg-opacity-90 transition-all"
              >
                검색하기
              </button>
            </div>
          </div>
        </form>
        
        {/* Quick Keywords */}
        <div className="mt-8 flex flex-col items-center w-full">
          <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">
            빠른 키워드 선택
          </p>
          <div className="flex flex-wrap justify-center items-center gap-2">
            {quickKeywords.map((keyword, index) => (
              <button
                key={keyword}
                onClick={() => {
                  setSearchQuery(keyword);
                  router.push(`${routes.search}?query=${encodeURIComponent(keyword)}`);
                }}
                className="flex h-10 items-center justify-center gap-x-2 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-5 text-sm font-medium hover:border-primary hover:text-primary transition-all shadow-sm"
              >
                <span className={`w-2 h-2 rounded-full ${
                  index === 0 ? 'bg-blue-400' : 
                  index === 1 ? 'bg-green-400' : 
                  'bg-orange-400'
                }`} />
                {keyword}
              </button>
            ))}
            
            <div className="w-px h-6 bg-gray-200 dark:bg-gray-700 mx-2" />
            
            {regions.map((region) => (
              <button
                key={region}
                onClick={() => {
                  router.push(`${routes.search}?region=${encodeURIComponent(region)}`);
                }}
                className="flex h-10 items-center justify-center px-5 rounded-full bg-gray-100 dark:bg-gray-800 text-sm font-medium hover:bg-gray-200 transition-all border border-transparent"
              >
                {region}
              </button>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

