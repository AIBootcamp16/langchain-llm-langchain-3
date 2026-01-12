/**
 * Policy Store
 * 정책 데이터 관리 스토어
 */

import { create } from 'zustand';
import type { Policy, PolicyListResponse } from '@/lib/types';

interface PolicyState {
  policies: Policy[];
  currentPolicy: Policy | null;
  total: number;
  page: number;
  size: number;
  loading: boolean;
  error: string | null;
  
  setPolicies: (data: PolicyListResponse) => void;
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
  
  setPolicies: (data) => set({
    policies: data.policies || [],
    total: data.total || 0,
    loading: false,
    error: null,
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
  }),
}));

