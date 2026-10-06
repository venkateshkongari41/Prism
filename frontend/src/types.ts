export type CacheType = "exact" | "semantic" | "miss" | null;

export interface UsageItem {
  id: number;
  application_id: number | null;
  application_name: string;
  model: string | null;
  provider: string | null;
  status: string;
  latency_ms: number | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  cost: number | null;
  created_at: string;
  request_id: string | null;
  cache_type: CacheType;
  fallback_used: boolean;
}

export interface UsageSummary {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost: number;
  average_latency_ms: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  fallback_requests: number;
  model_provider_breakdown: {
    model: string | null;
    provider: string | null;
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    total_tokens: number;
    total_cost: number;
  }[];
}

export interface UsageResponse {
  application: string;
  items: UsageItem[];
}

export interface SummaryResponse {
  application: string;
  summary: UsageSummary;
}
