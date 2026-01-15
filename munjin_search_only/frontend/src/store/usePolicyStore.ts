/**
 * Policy Store
 * 정책 데이터 관리 스토어
 */

import { create } from 'zustand';
import type { Policy, PolicyListResponse, SearchResponse, SearchMetrics, SearchEvidence } from '@/lib/types';

interface PolicyState {
  policies: Policy[];
  currentPolicy: Policy | null;
  total: number;
  page: number;
  size: number;
  loading: boolean;
  error: string | null;

  // 새로운 검색 관련 상태
  summary: string;
  topScore: number;
  isSufficient: boolean;
  sufficiencyReason: string;
  metrics: SearchMetrics | null;
  evidence: SearchEvidence[];
  searchTimeMs: number;

  setPolicies: (data: PolicyListResponse) => void;
  setSearchResult: (data: SearchResponse) => void;
  setCurrentPolicy: (policy: Policy | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const usePolicyStore = create<PolicyState>((set) => ({
  policies: [],
  currentPolicy: null,
  total: 0,
  page: 1,
  size: 10,
  loading: false,
  error: null,

  // 새로운 검색 관련 상태 초기값
  summary: '',
  topScore: 0,
  isSufficient: true,
  sufficiencyReason: '',
  metrics: null,
  evidence: [],
  searchTimeMs: 0,

  setPolicies: (data) => set({
    policies: data.policies || [],
    total: data.total || 0,
    loading: false,
    error: null,
  }),

  // 새로운 검색 결과 설정 (SimpleSearchService 응답용)
  setSearchResult: (data) => set({
    policies: data.policies || [],
    total: data.total_count || 0,
    summary: data.summary || '',
    topScore: data.top_score || 0,
    isSufficient: data.is_sufficient,
    sufficiencyReason: data.sufficiency_reason || '',
    metrics: data.metrics || null,
    evidence: data.evidence || [],
    searchTimeMs: data.metrics?.search_time_ms || 0,
    loading: false,
    error: data.error || null,
  }),

  setCurrentPolicy: (policy) => set({ currentPolicy: policy }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error, loading: false }),

  reset: () => set({
    policies: [],
    currentPolicy: null,
    total: 0,
    page: 1,
    size: 10,
    loading: false,
    error: null,
    summary: '',
    topScore: 0,
    isSufficient: true,
    sufficiencyReason: '',
    metrics: null,
    evidence: [],
    searchTimeMs: 0,
  }),
}));

