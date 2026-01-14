/**
 * Route Definitions
 * 앱 내 라우트 정의
 */

export const routes = {
  home: '/',
  search: '/search',
  policy: (policyId: number | string) => `/policy/${policyId}`,
  policyQA: (policyId: number | string) => `/policy/${policyId}/qa`,
  eligibilityStart: (policyId: number | string) => `/policy/${policyId}/eligibility/start`,
  eligibilityChecklist: (policyId: number | string) => `/policy/${policyId}/eligibility/checklist`,
  eligibilityResult: (policyId: number | string) => `/policy/${policyId}/eligibility/result`,
  sourceDetail: (sourceId: number | string) => `/sources/${sourceId}`,
} as const;

