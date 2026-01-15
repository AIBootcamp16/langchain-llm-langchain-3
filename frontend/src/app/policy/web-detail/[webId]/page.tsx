'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';

export default function WebPolicyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const webId = params.webId as string;
  const title = searchParams.get('title') || '';
  const url = searchParams.get('url') || '';
  const content = searchParams.get('content') || '';
  const screenshotUrl = searchParams.get('screenshot') || '';
  const faviconUrl = searchParams.get('favicon') || '';
  
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  
  // 본문 내용 자르기 (500자)
  const contentPreview = content.slice(0, 500);
  const hasMoreContent = content.length > 500;

  useEffect(() => {
    if (title && url && content) {
      console.log('=== 웹 상세 페이지 데이터 ===');
      console.log('screenshotUrl:', screenshotUrl);
      console.log('faviconUrl:', faviconUrl);
      setIsLoading(false);
    }
  }, [title, url, content, screenshotUrl, faviconUrl]);

  const handleQA = () => {
    try {
      console.log('=== Q&A 버튼 클릭됨 ===');
      console.log('webId:', webId);
      
      // 긴 content는 sessionStorage에 저장 (URL 길이 제한 회피)
      const webPolicyData = {
        webId,
        title,
        url,
        content
      };
      
      sessionStorage.setItem(`webPolicy_${webId}`, JSON.stringify(webPolicyData));
      console.log('sessionStorage에 저장 완료');
      
      // 짧은 URL로 이동
      const qaUrl = `/policy/web/qa?webId=${webId}`;
      console.log('이동할 URL:', qaUrl);
      
      router.push(qaUrl);
      console.log('이동 완료');
    } catch (error) {
      console.error('에러 발생:', error);
      alert('에러: ' + error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-text-muted">웹 공고를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="flex-1 w-full max-w-[1200px] mx-auto px-6 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* 왼쪽: 웹 공고 상세 정보 */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {/* 헤더 */}
          <div className="bg-white dark:bg-gray-900 rounded-xl overflow-hidden border border-[#eaf0ef] dark:border-gray-800 shadow-sm">
            {/* 스크린샷 */}
            {screenshotUrl && (
              <div className="relative w-full h-64 bg-gray-100 dark:bg-gray-800 overflow-hidden">
                <img 
                  src={screenshotUrl}
                  alt={title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    // 스크린샷 로드 실패 시 숨김
                    e.currentTarget.parentElement!.style.display = 'none';
                  }}
                />
                {/* 웹 검색 배지 */}
                <div className="absolute top-4 right-4 bg-white/95 dark:bg-gray-800/95 px-4 py-2 rounded-full text-sm font-bold flex items-center gap-2 shadow-lg">
                  <span className="material-symbols-outlined text-[20px] text-green-600">language</span>
                  <span className="text-green-700 dark:text-green-400">웹 검색</span>
                </div>
              </div>
            )}
            
            <div className="bg-gradient-to-r from-primary/10 to-primary/5 p-6 border-b border-[#eaf0ef] dark:border-gray-800">
              <div className="flex items-center gap-3 mb-3">
                <span className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs font-bold rounded">
                  웹 검색
                </span>
                <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-bold rounded">
                  웹 공고
                </span>
              </div>
              <div className="flex items-start gap-3 mb-4">
                {faviconUrl && (
                  <img 
                    src={faviconUrl}
                    alt="favicon"
                    className="w-10 h-10 rounded mt-1 shrink-0"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                )}
                <h1 className="text-2xl font-bold text-text-primary dark:text-white">
                  {title}
                </h1>
              </div>
              <div className="flex items-center gap-2 text-sm text-text-muted dark:text-gray-400">
                <span className="material-symbols-outlined text-[18px]">link</span>
                <a 
                  href={url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="hover:text-primary hover:underline transition-colors break-all"
                >
                  {url}
                </a>
              </div>
            </div>

            {/* 본문 내용 */}
            <div className="p-6">
              <div className="prose dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-text-secondary dark:text-gray-300 leading-relaxed">
                  {isExpanded ? content : contentPreview}
                  {!isExpanded && hasMoreContent && (
                    <span className="text-text-muted">...</span>
                  )}
                </div>
                
                {/* 더 보기 / 접기 버튼 */}
                {hasMoreContent && (
                  <div className="mt-4 flex justify-center">
                    <button
                      onClick={() => setIsExpanded(!isExpanded)}
                      className="px-6 py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-text-primary dark:text-white rounded-lg font-bold text-sm transition-all flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-[20px]">
                        {isExpanded ? 'expand_less' : 'expand_more'}
                      </span>
                      {isExpanded ? '접기' : '더 보기'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 원문 보기 버튼 */}
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-[#eaf0ef] dark:border-gray-800 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-text-primary dark:text-white mb-2">
                  원문 확인하기
                </h3>
                <p className="text-sm text-text-muted dark:text-gray-400">
                  자세한 내용은 원본 웹사이트에서 확인하세요
                </p>
              </div>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 text-text-primary dark:text-white px-6 py-3 rounded-lg font-bold text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-all"
              >
                <span className="material-symbols-outlined text-[20px]">open_in_new</span>
                원문 보기
              </a>
            </div>
          </div>
        </div>

        {/* 오른쪽: 사이드바 (Q&A 버튼) */}
        <aside className="lg:col-span-4 sticky top-4 flex flex-col gap-4">
          {/* Q&A 버튼 */}
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-[#eaf0ef] dark:border-gray-800 shadow-sm">
            <div className="flex flex-col gap-4">
              <button
                onClick={handleQA}
                className="group relative flex flex-col items-start gap-1 w-full bg-white dark:bg-gray-800 border-2 border-primary text-primary dark:text-white p-5 rounded-xl transition-all hover:bg-primary/5"
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-lg font-extrabold">AI에게 질문하기 ▶</span>
                  <span className="material-symbols-outlined group-hover:scale-110 transition-transform">chat_bubble</span>
                </div>
                <p className="text-text-muted dark:text-gray-400 text-xs font-medium">Q&A with AI Assistant</p>
              </button>
            </div>
          </div>

          {/* 안내 카드 */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-[24px]">info</span>
              <div>
                <h4 className="font-bold text-blue-900 dark:text-blue-300 mb-2">웹 공고 안내</h4>
                <p className="text-sm text-blue-700 dark:text-blue-400 leading-relaxed">
                  이 정보는 웹 검색 결과입니다. 정확한 내용은 원문을 확인해주세요.
                </p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}

