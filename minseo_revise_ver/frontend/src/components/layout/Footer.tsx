/**
 * Footer Component
 * 앱 푸터 - Stitch 디자인 적용
 */

import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-6 flex flex-col items-center justify-center gap-4">
        <div className="flex items-center gap-2 py-2 px-4 bg-primary/5 rounded-full border border-primary/10">
          <span className="material-symbols-outlined text-primary text-[18px]">info</span>
          <p className="text-primary text-xs md:text-sm font-medium leading-normal">
            근거 없는 답변은 제공하지 않습니다. 모든 정보는 공식 데이터를 기반으로 합니다.
          </p>
        </div>
        <div className="flex gap-6 text-gray-400 text-xs mt-2">
          <a className="hover:underline" href="#">이용약관</a>
          <a className="hover:underline" href="#">개인정보처리방침</a>
          <p>© 2024 Policy Assistant AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

