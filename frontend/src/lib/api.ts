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
 * Q&A 채팅 (Non-streaming)
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/api/v1/chat', request);
  return response.data;
};

/**
 * Q&A 채팅 (Streaming)
 * 
 * SSE (Server-Sent Events)를 사용한 실시간 스트리밍
 * 
 * @param request - 채팅 요청
 * @param onChunk - 답변 청크 수신 시 호출되는 콜백
 * @param onStatus - 상태 업데이트 시 호출되는 콜백
 * @param onEvidence - Evidence 수신 시 호출되는 콜백
 * @param onError - 에러 발생 시 호출되는 콜백
 * @param onDone - 완료 시 호출되는 콜백
 */
export const sendChatMessageStream = async (
  request: ChatRequest,
  callbacks: {
    onChunk?: (chunk: string) => void;
    onStatus?: (status: { step: string; message: string }) => void;
    onEvidence?: (evidence: any[]) => void;
    onError?: (error: string) => void;
    onDone?: () => void;
  }
): Promise<void> => {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = `${baseURL}/api/v1/chat/stream`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  if (!reader) {
    throw new Error('Response body is not readable');
  }
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('event:')) {
          const eventType = line.substring(6).trim();
          continue;
        }
        
        if (line.startsWith('data:')) {
          const data = line.substring(5).trim();
          
          if (!data) continue;
          
          try {
            const parsed = JSON.parse(data);
            
            // 이벤트 타입에 따라 콜백 호출
            if (parsed.content && callbacks.onChunk) {
              callbacks.onChunk(parsed.content);
            } else if (parsed.step && callbacks.onStatus) {
              callbacks.onStatus(parsed);
            } else if (parsed.evidence && callbacks.onEvidence) {
              callbacks.onEvidence(parsed.evidence);
            } else if (parsed.message === '완료' && callbacks.onDone) {
              callbacks.onDone();
            } else if (parsed.message && parsed.code && callbacks.onError) {
              // 에러 이벤트 (code 포함)
              callbacks.onError(parsed);
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }
    }
  } catch (error) {
    if (callbacks.onError) {
      callbacks.onError(error instanceof Error ? error.message : String(error));
    }
    throw error;
  } finally {
    reader.releaseLock();
  }
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
 * 웹 공고 캐시 초기화 (웹 검색 결과 클릭 시)
 */
export const initWebPolicy = async (
  sessionId: string,
  webId: string,
  title: string,
  url: string,
  content: string
): Promise<void> => {
  await apiClient.post('/api/v1/chat/init-web-policy', {
    session_id: sessionId,
    web_id: webId,
    title: title,
    url: url,
    content: content,
    source: '웹 검색',
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

