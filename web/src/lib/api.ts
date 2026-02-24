const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

// --- Types ---

export interface CallOut {
  id: string;
  customer_id: string;
  gong_call_id: string | null;
  title: string;
  date: string;
  duration_seconds: number | null;
  participants: string[];
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

export interface CallDetail extends CallOut {
  raw_transcript: string;
  chunks: ChunkOut[];
  fields: FieldOut[];
  summary: SummaryOut | null;
}

export interface AnalyticsOverview {
  total_calls: number;
  total_chunked: number;
  field_distributions: { field_name: string; values: Record<string, number> }[];
}

export interface CustomerConfig {
  slug: string;
  display_name: string;
  industry: string;
  config_path: string;
}

// --- API Functions ---

export const api = {
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
  getOverview: (customerSlug?: string) =>
    fetchAPI<AnalyticsOverview>(
      `/api/v1/analytics/overview${
        customerSlug ? `?customer_slug=${customerSlug}` : ""
      }`
    ),

  getPainPoints: (customerSlug?: string) =>
    fetchAPI<{ field: string; counts: Record<string, number>; total_calls: number }>(
      `/api/v1/analytics/pain-points${
        customerSlug ? `?customer_slug=${customerSlug}` : ""
      }`
    ),

  getCompetitors: (customerSlug?: string) =>
    fetchAPI<{ field: string; counts: Record<string, number>; total_calls: number }>(
      `/api/v1/analytics/competitors${
        customerSlug ? `?customer_slug=${customerSlug}` : ""
      }`
    ),

  getDealLikelihood: (customerSlug?: string) =>
    fetchAPI<any>(
      `/api/v1/analytics/deal-likelihood${
        customerSlug ? `?customer_slug=${customerSlug}` : ""
      }`
    ),

  getSentiment: (customerSlug?: string) =>
    fetchAPI<any>(
      `/api/v1/analytics/sentiment${
        customerSlug ? `?customer_slug=${customerSlug}` : ""
      }`
    ),
};
