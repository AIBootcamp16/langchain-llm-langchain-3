/**
 * Eligibility Store
 * 자격 확인 상태 관리 스토어 (Q&A 방식)
 */

import { create } from 'zustand';
import type { EligibilityResult } from '@/lib/types';

interface Progress {
  current: number;
  total: number;
}

interface CurrentQuestion {
  question: string;
  options?: string[];
}

interface EligibilityState {
  // 세션 정보
  sessionId: string | null;
  policyId: number | null;

  // Q&A 데이터
  currentQuestion: CurrentQuestion | null;
  progress: Progress | null;
  answers: string[];

  // 결과 및 상태 정보
  result: EligibilityResult | null;
  loading: boolean;
  error: string | null;

  // Actions
  setSession: (sessionId: string, policyId: number) => void;
  setQuestion: (question: string, progress: Progress, options?: string[]) => void;
  addAnswer: (answer: string) => void;
  setResult: (result: EligibilityResult) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useEligibilityStore = create<EligibilityState>((set) => ({
  sessionId: null,
  policyId: null,
  currentQuestion: null,
  progress: null,
  answers: [],
  result: null,
  loading: false,
  error: null,

  setSession: (sessionId, policyId) => set({
    sessionId,
    policyId,
    error: null
  }),

  setQuestion: (question, progress, options) => set({
    currentQuestion: { question, options },
    progress,
    loading: false
  }),

  addAnswer: (answer) => set((state) => ({
    answers: [...state.answers, answer]
  })),

  setResult: (result) => set({ result, loading: false }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error, loading: false }),

  reset: () => set({
    sessionId: null,
    policyId: null,
    currentQuestion: null,
    progress: null,
    answers: [],
    result: null,
    loading: false,
    error: null,
  }),
}));