export interface Policy {
  id: number;
  program_name: string;
  region: string;
  category: string;
  program_overview: string;
  support_description: string;
  supervising_ministry: string;
  score?: number;
  [key: string]: any;
}

export interface PolicyListResponse {
  policies: Policy[];
  total: number;
}

export interface EligibilityResult {
  eligible: boolean;
  requirements: { requirement: string; met: boolean }[];
}