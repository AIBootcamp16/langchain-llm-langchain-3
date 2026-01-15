'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ExternalLink, Calendar, Globe, ArrowLeft, Loader2 } from 'lucide-react';

interface WebSource {
  id: number;
  url: string;
  title: string;
  snippet: string | null;
  content: string | null;
  source_type: string;
  fetched_date: string | null;
  created_at: string;
}

export default function WebSourceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sourceId = params?.sourceId as string;

  const [webSource, setWebSource] = useState<WebSource | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sourceId) return;

    const fetchWebSource = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/web-source/${sourceId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('웹 근거를 찾을 수 없습니다.');
          }
          throw new Error('웹 근거를 불러오는 중 오류가 발생했습니다.');
        }

        const data = await response.json();
        setWebSource(data);
      } catch (err) {
        console.error('Error fetching web source:', err);
        setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchWebSource();
  }, [sourceId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-muted flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">웹 근거를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error || !webSource) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-muted flex items-center justify-center">
        <div className="max-w-md w-full mx-auto px-6 text-center">
          <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-8">
            <h1 className="text-2xl font-bold text-destructive mb-2">오류 발생</h1>
            <p className="text-muted-foreground mb-6">{error || '웹 근거를 찾을 수 없습니다.'}</p>
            <button
              onClick={() => router.back()}
              className="bg-primary hover:bg-[#1f534a] text-white px-6 py-2.5 rounded-lg font-bold transition-all"
            >
              돌아가기
            </button>
          </div>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '알 수 없음';
    try {
      return new Date(dateString).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const getSourceTypeName = (type: string) => {
    switch (type.toLowerCase()) {
      case 'tavily':
        return 'Tavily 웹 검색';
      case 'duckduckgo':
        return 'DuckDuckGo 검색';
      default:
        return '웹 검색';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      {/* Header */}
      <header className="border-b bg-white/50 dark:bg-[#1a1e1e]/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">돌아가기</span>
          </button>
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-2 rounded-lg">
              <Globe className="w-6 h-6 text-primary" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">
                {getSourceTypeName(webSource.source_type)}
              </div>
              <h1 className="text-2xl font-bold text-foreground line-clamp-1">
                {webSource.title}
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Source Info Card */}
        <div className="bg-white dark:bg-[#242828] rounded-xl border border-border/50 p-6 space-y-4">
          {/* URL */}
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 block">
              원본 URL
            </label>
            <a
              href={webSource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-primary hover:text-[#1f534a] transition-colors group"
            >
              <span className="break-all">{webSource.url}</span>
              <ExternalLink className="w-4 h-4 flex-shrink-0 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </a>
          </div>

          {/* Metadata */}
          <div className="flex flex-wrap gap-4 pt-4 border-t border-border/30">
            {webSource.fetched_date && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="w-4 h-4" />
                <span>조회일: {formatDate(webSource.fetched_date)}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="w-4 h-4" />
              <span>수집일: {formatDate(webSource.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Snippet */}
        {webSource.snippet && (
          <div className="bg-white dark:bg-[#242828] rounded-xl border border-border/50 p-6">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              요약
            </h2>
            <p className="text-foreground leading-relaxed">{webSource.snippet}</p>
          </div>
        )}

        {/* Full Content */}
        {webSource.content && (
          <div className="bg-white dark:bg-[#242828] rounded-xl border border-border/50 p-6">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
              전체 내용
            </h2>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <div className="text-foreground leading-relaxed whitespace-pre-wrap">
                {webSource.content}
              </div>
            </div>
          </div>
        )}

        {/* Visit Source Button */}
        <div className="flex justify-center pt-4">
          <a
            href={webSource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-primary hover:bg-[#1f534a] text-white px-8 py-3 rounded-lg font-bold text-sm flex items-center gap-2 transition-all shadow-lg hover:shadow-xl"
          >
            <span>원문 보기</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </main>
    </div>
  );
}

