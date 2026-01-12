/**
 * Header Component
 * 앱 헤더 - Stitch 디자인 적용
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { routes } from '@/lib/routes';

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 w-full bg-white/80 dark:bg-background-dark/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-primary text-white p-1.5 rounded-lg flex items-center justify-center">
            <span className="material-symbols-outlined text-xl">account_balance</span>
          </div>
          <Link href={routes.home}>
            <h2 className="text-lg font-bold leading-tight tracking-tight hover:text-primary transition-colors">
              정책·지원금 AI 도우미
            </h2>
          </Link>
        </div>
        <div className="flex items-center gap-6">
          <nav className="hidden md:flex items-center gap-8">
            <Link
              href={routes.home}
              className="text-sm font-semibold hover:text-primary transition-colors flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-[18px]">home</span> Home
            </Link>
          </nav>
          <button className="bg-primary hover:bg-primary/90 text-white text-sm font-bold py-2 px-5 rounded-lg transition-all shadow-sm">
            Login
          </button>
        </div>
      </div>
    </header>
  );
};

