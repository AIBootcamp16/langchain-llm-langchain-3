/**
 * Eligibility Store
 * 자격 확인 상태 관리 스토어 (체크리스트 방식 고도화 버전)
 */

import { create } from 'zustand';
import type { EligibilityResult } from '@/lib/types';

// 1. 체크리스트 개별 항목 타입 정의
interface ChecklistItem {
  condition_index: number;
  label: string;
  selection: 'PASS' | 'FAIL' | 'UNKNOWN' | null;
}

interface EligibilityState {
  // 세션 정보
  sessionId: string | null;
  policyId: number | null;
  
  // 체크리스트 데이터 (기존 currentQuestion, answers 대체)
  checklist: ChecklistItem[]; 
  extraRequirements: string | null;
  
  // 결과 및 상태 정보
  result: EligibilityResult | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  // /start API 호출 결과를 저장하는 함수
  setStartData: (
    sessionId: string, 
    policyId: number, 
    checklist: ChecklistItem[], 
    extraRequirements?: string | null
  ) => void;
  
  // 사용자가 화면에서 체크박스를 선택할 때 호출하는 함수
  updateSelection: (index: number, selection: 'PASS' | 'FAIL' | 'UNKNOWN') => void;
  
  setResult: (result: EligibilityResult) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useEligibilityStore = create<EligibilityState>((set) => ({
  sessionId: null,
  policyId: null,
  checklist: [],
  extraRequirements: null,
  result: null,
  loading: false,
  error: null,
  
  // 초기 데이터 세팅: 질문 기반에서 체크리스트 기반으로 변경
  setStartData: (sessionId, policyId, checklist, extraRequirements) => set({ 
    sessionId, 
    policyId, 
    checklist, 
    extraRequirements: extraRequirements || null,
    loading: false,
    error: null
  }),
  
  // 특정 인덱스의 체크박스 상태만 업데이트
  updateSelection: (index, selection) => set((state) => ({
    checklist: state.checklist.map((item) => 
      item.condition_index === index ? { ...item, selection } : item
    )
  })),
  
  setResult: (result) => set({ result, loading: false }),
  
  setLoading: (loading) => set({ loading }),
  
  setError: (error) => set({ error, loading: false }),
  
  reset: () => set({
    sessionId: null,
    policyId: null,
    checklist: [],
    extraRequirements: null,
    result: null,
    loading: false,
    error: null,
  }),
}));