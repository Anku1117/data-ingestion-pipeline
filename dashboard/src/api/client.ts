const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

export interface Event {
  event_id: string;
  event_type: string;
  source: string;
  producer: string;
  severity: string;
  timestamp: string;
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
  agent_id?: string;
  run_id?: string;
}

export interface ThreatAlert {
  alert_id: string;
  threat_type: string;
  severity: string;
  confidence: number;
  timestamp: string;
  source: string;
  description: string;
  event_ids: string[];
}

export interface AgentRun {
  run_id: string;
  task_id: string;
  agent_id: string;
  status: string;
  started_at: string;
  ended_at?: string;
  outcome?: string;
  total_tokens: number;
  total_steps: number;
}

export interface PipelineStatus {
  status: string;
  event_backend: { type: string; healthy: boolean };
  search_backend: { type: string; healthy: boolean };
  metrics: Record<string, number>;
}

export interface PaginatedResult<T> {
  total: number;
  events?: T[];
  alerts?: T[];
  runs?: T[];
  evaluations?: T[];
  limit: number;
  offset: number;
}

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getHealth: () => fetchApi<{ status: string; version: string; environment: string }>("/health"),
  getReady: () => fetchApi<{ status: string; database: string }>("/ready"),

  getEvents: (params?: { event_type?: string; source?: string; severity?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.event_type) q.set("event_type", params.event_type);
    if (params?.source) q.set("source", params.source);
    if (params?.severity) q.set("severity", params.severity);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    return fetchApi<PaginatedResult<Event>>(`/events?${q.toString()}`);
  },

  getEvent: (eventId: string) => fetchApi<Event>(`/events/${eventId}`),

  getThreats: (params?: { threat_type?: string; severity?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.threat_type) q.set("threat_type", params.threat_type);
    if (params?.severity) q.set("severity", params.severity);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    return fetchApi<PaginatedResult<ThreatAlert>>(`/threats?${q.toString()}`);
  },

  getThreatStats: () => fetchApi<{ total_alerts: number; active_rules: number; rules: Array<{ name: string; description: string }> }>("/threats/stats"),

  getRuns: (params?: { agent_id?: string; status?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.agent_id) q.set("agent_id", params.agent_id);
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    return fetchApi<PaginatedResult<AgentRun>>(`/agents/runs?${q.toString()}`);
  },

  getRun: (runId: string) => fetchApi<AgentRun>(`/agents/runs/${runId}`),

  getTrajectory: (runId: string) => fetchApi<unknown>(`/agents/runs/${runId}/trajectory`),

  getEvaluations: (params?: { agent_id?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.agent_id) q.set("agent_id", params.agent_id);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    return fetchApi<PaginatedResult<unknown>>(`/agents/evaluations?${q.toString()}`);
  },

  getPipelineStatus: () => fetchApi<PipelineStatus>("/pipeline/status"),
  getPipelineStats: () => fetchApi<Record<string, unknown>>("/pipeline/stats"),
  getMetrics: () => fetchApi<{ counters: Record<string, number>; timers: Record<string, unknown> }>("/metrics"),
};
