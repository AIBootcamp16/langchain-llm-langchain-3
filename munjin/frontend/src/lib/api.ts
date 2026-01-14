/**
 * API Client
 * 백엔드 API 호출 함수들
 */

import axios, { AxiosInstance } from 'axios';
import type {
  Policy,
  PolicyListResponse,
  ChatRequest,
  ChatResponse,
  EligibilityStartRequest,
  EligibilityStartResponse,
  EligibilityAnswerRequest,
  EligibilityAnswerResponse,
  EligibilityResult,
  SearchParams,
} from './types';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 120000, // 120초 (2분) - LLM 응답 생성 시간 고려
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================
// Policy APIs
// ============================================================

/**
 * 정책 목록 조회
 */
export const getPolicies = async (params: SearchParams = {}): Promise<PolicyListResponse> => {
  const response = await apiClient.get<PolicyListResponse>('/api/v1/policies', { params });
  return response.data;
};

/**
 * 정책 상세 조회
 */
export const getPolicy = async (policyId: number): Promise<Policy> => {
  const response = await apiClient.get<Policy>(`/api/v1/policy/${policyId}`);
  return response.data;
};

/**
 * 지역 목록 조회
 */
export const getRegions = async (): Promise<string[]> => {
  const response = await apiClient.get<string[]>('/api/v1/policies/regions');
  return response.data;
};

/**
 * 카테고리 목록 조회
 */
export const getCategories = async (): Promise<string[]> => {
  const response = await apiClient.get<string[]>('/api/v1/policies/categories');
  return response.data;
};

// ============================================================
// Chat APIs
// ============================================================

/**
 * Q&A 채팅
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/api/v1/chat', request);
  return response.data;
};

/**
 * 정책 문서 초기화 (캐시에 저장)
 */
export const initPolicy = async (sessionId: string, policyId: number): Promise<void> => {
  await apiClient.post('/api/v1/chat/init-policy', {
    session_id: sessionId,
    policy_id: policyId,
  });
};

/**
 * 채팅 캐시 정리 (대화창 나갈 때)
 */
export const cleanupSession = async (sessionId: string): Promise<void> => {
  await apiClient.post('/api/v1/chat/cleanup', {
    session_id: sessionId,
  });
};

/**
 * 세션 초기화
 */
export const resetSession = async (sessionId: string): Promise<void> => {
  await apiClient.post('/api/v1/session/reset', { session_id: sessionId });
};

// ============================================================
// Eligibility APIs
// ============================================================

/**
 * 자격 확인 시작
 */
export const startEligibilityCheck = async (
  request: EligibilityStartRequest
): Promise<EligibilityStartResponse> => {
  const response = await apiClient.post<EligibilityStartResponse>(
    '/api/v1/eligibility/start',
    request
  );
  return response.data;
};

/**
 * 자격 확인 답변
 */
export const answerEligibilityQuestion = async (
  request: EligibilityAnswerRequest
): Promise<EligibilityAnswerResponse> => {
  const response = await apiClient.post<EligibilityAnswerResponse>(
    '/api/v1/eligibility/answer',
    request
  );
  return response.data;
};

/**
 * 자격 확인 결과 조회
 */
export const getEligibilityResult = async (sessionId: string): Promise<EligibilityResult> => {
  const response = await apiClient.get<EligibilityResult>(
    `/api/v1/eligibility/result/${sessionId}`
  );
  return response.data;
};

/**
 * 자격 확인 세션 삭제
 */
export const deleteEligibilitySession = async (sessionId: string): Promise<void> => {
  await apiClient.delete(`/api/v1/eligibility/session/${sessionId}`);
};

// ============================================================
// Error Handler
// ============================================================

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
