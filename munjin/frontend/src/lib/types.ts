/**
 * Type Definitions
 * 전역 타입 정의
 */

// ============================================================
// Policy Types
// ============================================================

export interface Policy {
  id: number;
  program_id: number;
  region: string;
  category: string;
  program_name: string;
  program_overview?: string;
  support_description: string;
  support_budget?: number;
  support_scale?: string;
  supervising_ministry?: string;
  apply_target: string;
  announcement_date?: string;
  biz_process?: string;
  application_method?: string;
  contact_agency?: string;
  contact_number?: string[];
  required_documents?: string[];
  collected_date?: string;
  support_details?: string;
  apply_method?: string;
  contact?: string;
  url?: string;
  created_at: string;
  updated_at?: string;
  score?: number | null;
}

export interface PolicyListResponse {
  policies: Policy[];
  total: number;
  count: number;
  offset: number;
  limit: number;
}

// ============================================================
// Evidence Types
// ============================================================

export type EvidenceType = 'policy_doc' | 'web_source';

export interface Evidence {
  type: EvidenceType;
  policy_id?: number;
  document_id?: number;
  chunk_id?: string;
  content: string;
  score?: number;
  url?: string;
  title?: string;
}

// ============================================================
// Chat Types
// ============================================================

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  evidence?: Evidence[];
  timestamp?: string;
}

export interface ChatRequest {
  session_id?: string;
  message: string;
  policy_id?: number;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  evidence: Evidence[];
  web_sources: any[];
}

// ============================================================
// Eligibility Types
// ============================================================

export interface EligibilityStartRequest {
  session_id?: string;
  policy_id: number;
}

export interface EligibilityQuestion {
  question: string;
  options?: string[];
}

export interface EligibilityStartResponse {
  session_id: string;
  policy_id: number;
  question: string;
  options?: string[];
  progress: {
    current: number;
    total: number;
  };
}

export interface EligibilityAnswerRequest {
  session_id: string;
  answer: string;
}

export interface EligibilityAnswerResponse {
  session_id: string;
  question?: string;
  options?: string[];
  progress: {
    current: number;
    total: number;
  };
  completed: boolean;
}

export interface ConditionResult {
  condition: string;
  status: 'PASS' | 'FAIL' | 'UNKNOWN';
  reason: string;
}

export interface EligibilityResult {
  session_id: string;
  policy_id: number;
  eligible: boolean;
  result: 'ELIGIBLE' | 'NOT_ELIGIBLE' | 'PARTIALLY';
  reason: string;
  requirements: Array<{
    requirement: string;
    met: boolean;
  }>;
  details?: ConditionResult[];
}

// ============================================================
// Search Types
// ============================================================

export interface SearchParams {
  query?: string;
  region?: string;
  category?: string;
  page?: number;
  size?: number;
