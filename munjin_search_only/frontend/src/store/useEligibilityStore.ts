/**
 * Eligibility Store
 * 자격 확인 상태 관리 스토어
 */

import { create } from 'zustand';
import type { EligibilityResult } from '@/lib/types';

interface EligibilityState {
  sessionId: string | null;
  policyId: number | null;
  currentQuestion: { question: string; options?: string[] } | null;
  progress: { current: number; total: number } | null;
  answers: string[];
  result: EligibilityResult | null;
  loading: boolean;
  error: string | null;
  
  setSession: (sessionId: string, policyId: number) => void;
  setQuestion: (question: string, progress: { current: number; total: number }, options?: string[]) => void;
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
  
  setSession: (sessionId, policyId) => set({ sessionId, policyId }),
  
  setQuestion: (question, progress, options) => set({
    currentQuestion: { question, options },
    progress,
    loading: false,
  }),
  
  addAnswer: (answer) => set((state) => ({
    answers: [...state.answers, answer],
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

