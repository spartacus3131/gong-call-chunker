// Use relative URLs so Next.js rewrites proxy to the backend (avoids CORS)
async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (res.status === 401) {
    window.location.href = "/api/auth/signin";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

// --- Types ---

export interface UserInfo {
  id: string | null;
  email: string;
  name: string;
  picture: string | null;
  has_completed_onboarding: boolean;
  authenticated: boolean;
}

export interface CallOut {
  id: string;
  customer_id: string;
  gong_call_id: string | null;
  title: string;
  date: string;
  duration_seconds: number | null;
  participants: string[];
  rep_name: string | null;
  rep_email: string | null;
  status: string;
  error_message: string | null;
  processed_at: string | null;
  created_at: string;
}

export interface ChunkOut {
  id: string;
  level: string;
  content: Record<string, any>;
  timestamp_start: string | null;
  timestamp_end: string | null;
}

export interface FieldOut {
  id: string;
  field_name: string;
  field_value: any;
  field_type: string;
}

export interface SummaryOut {
  overall_sentiment: string | null;
  deal_likelihood: number | null;
  next_steps: string[];
  follow_up_date: string | null;
  summary_text: string | null;
}

export interface ScoreOut {
  id: string;
  skill_name: string;
  skill_category: string;
  score: number;
  evidence: string | null;
  present: boolean;
}

export interface CallDetail extends CallOut {
  raw_transcript: string;
  chunks: ChunkOut[];
  fields: FieldOut[];
  summary: SummaryOut | null;
  scores: ScoreOut[];
}

export interface AnalyticsOverview {
  total_calls: number;
  total_chunked: number;
  field_distributions: { field_name: string; values: Record<string, number> }[];
}

export interface CustomerConfig {
  slug: string;
  display_name: string;
  config_path: string;
}

export interface SkillAverage {
  skill_name: string;
  skill_category: string;
  avg_score: number;
  times_present: number;
  total_calls: number;
}

export interface ScorecardOverview {
  skill_averages: SkillAverage[];
  total_scored_calls: number;
  categories: { key: string; label: string }[];
}

export interface SkillCorrelation {
  skill_name: string;
  avg_deal_when_present: number | null;
  avg_deal_when_absent: number | null;
  lift: number | null;
  calls_present: number;
  calls_absent: number;
}

export interface IndustryTemplate {
  key: string;
  display_name: string;
  industry: string;
  field_count: number;
}

export interface TemplateDetail {
  display_name: string;
  industry: string;
  fields: {
    name: string;
    type: string;
    description?: string;
    options?: string[];
    examples?: string[];
  }[];
}

// --- Helpers ---

function _analyticsParams(customerSlug?: string, repName?: string): string {
  const params = new URLSearchParams();
  if (customerSlug) params.set("customer_slug", customerSlug);
  if (repName) params.set("rep_name", repName);
  const str = params.toString();
  return str ? `?${str}` : "";
}

// --- API Functions ---

export const api = {
  // User
  getMe: () => fetchAPI<UserInfo>("/api/v1/me"),

  updateMe: (data: { has_completed_onboarding?: boolean; name?: string }) =>
    fetchAPI("/api/v1/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Templates
  listTemplates: () => fetchAPI<IndustryTemplate[]>("/api/v1/templates"),

  getTemplate: (industry: string) =>
    fetchAPI<TemplateDetail>(`/api/v1/templates/${industry}`),

  // Calls
  listCalls: (customerSlug?: string) =>
    fetchAPI<CallOut[]>(
      `/api/v1/calls${customerSlug ? `?customer_slug=${customerSlug}` : ""}`
    ),

  getCall: (id: string) => fetchAPI<CallDetail>(`/api/v1/calls/${id}`),

  createCall: (data: {
    customer_slug: string;
    title: string;
    date: string;
    raw_transcript: string;
    participants?: string[];
    rep_name?: string;
  }) =>
    fetchAPI<CallOut>("/api/v1/calls", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  chunkCall: (id: string) =>
    fetchAPI<CallDetail>(`/api/v1/calls/${id}/chunk`, { method: "POST" }),

  deleteCall: (id: string) =>
    fetchAPI(`/api/v1/calls/${id}`, { method: "DELETE" }),

  // Chunks
  searchCalls: (body: {
    query?: string;
    customer_slug?: string;
    filters?: Record<string, any>;
  }) =>
    fetchAPI<{ calls: CallOut[]; total: number }>("/api/v1/chunks/search", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  searchQuotes: (q: string, customerSlug?: string) =>
    fetchAPI<any[]>(
      `/api/v1/chunks/search/quotes?q=${encodeURIComponent(q)}${
        customerSlug ? `&customer_slug=${customerSlug}` : ""
      }`
    ),

  // Schemas
  listSchemas: () => fetchAPI<CustomerConfig[]>("/api/v1/schemas"),

  getSchema: (slug: string) => fetchAPI<any>(`/api/v1/schemas/${slug}`),

  updateSchema: (slug: string, data: any) =>
    fetchAPI(`/api/v1/schemas/${slug}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  createSchema: (data: any) =>
    fetchAPI("/api/v1/schemas", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Analytics
  getReps: (customerSlug?: string) =>
    fetchAPI<string[]>(
      `/api/v1/analytics/reps${
        customerSlug ? `?customer_slug=${customerSlug}` : ""
      }`
    ),

  getOverview: (customerSlug?: string, repName?: string) =>
    fetchAPI<AnalyticsOverview>(
      `/api/v1/analytics/overview${_analyticsParams(customerSlug, repName)}`
    ),

  getPainPoints: (customerSlug?: string, repName?: string) =>
    fetchAPI<{ field: string; counts: Record<string, number>; total_calls: number }>(
      `/api/v1/analytics/pain-points${_analyticsParams(customerSlug, repName)}`
    ),

  getCompetitors: (customerSlug?: string, repName?: string) =>
    fetchAPI<{ field: string; counts: Record<string, number>; total_calls: number }>(
      `/api/v1/analytics/competitors${_analyticsParams(customerSlug, repName)}`
    ),

  getDealLikelihood: (customerSlug?: string, repName?: string) =>
    fetchAPI<any>(
      `/api/v1/analytics/deal-likelihood${_analyticsParams(customerSlug, repName)}`
    ),

  getSentiment: (customerSlug?: string, repName?: string) =>
    fetchAPI<any>(
      `/api/v1/analytics/sentiment${_analyticsParams(customerSlug, repName)}`
    ),

  getScorecard: (customerSlug?: string, repName?: string) =>
    fetchAPI<ScorecardOverview>(
      `/api/v1/analytics/scorecard${_analyticsParams(customerSlug, repName)}`
    ),

  getScorecardCorrelation: (customerSlug?: string, repName?: string) =>
    fetchAPI<{ correlations: SkillCorrelation[]; total_calls: number }>(
      `/api/v1/analytics/scorecard/correlation${_analyticsParams(customerSlug, repName)}`
    ),
};
