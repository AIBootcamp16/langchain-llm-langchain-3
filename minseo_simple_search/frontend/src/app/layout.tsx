/**
 * Root Layout
 * 앱 전체 레이아웃
 */

import type { Metadata } from 'next';
import { Manrope } from 'next/font/google';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import '@/styles/globals.css';

const manrope = Manrope({ 
  subsets: ['latin'],
  weight: ['400', '500', '700', '800'],
  variable: '--font-manrope',
});

export const metadata: Metadata = {
  title: '정책·지원금 AI 도우미',
  description: '정부 정책·지원금 정보를 쉽게 탐색하고, 근거 기반 설명 + 자격 가능성 판단을 제공합니다.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className="light">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${manrope.variable} font-display bg-background-light dark:bg-background-dark text-[#111817] dark:text-gray-100 min-h-screen`}>
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
        {/* Background decorative elements */}
        <div className="fixed top-1/4 -left-20 w-96 h-96 bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
        <div className="fixed bottom-1/4 -right-20 w-80 h-80 bg-primary/5 rounded-full blur-[80px] pointer-events-none" />
      </body>
    </html>
  );
}

