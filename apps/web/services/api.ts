import type {
  DatasetSample,
  EvaluationDraft,
  LeaderboardEntry,
  ManagerSnapshot,
  ModelConfig,
  Suggestion,
  TaskDetail,
  TaskSummary,
  User
} from "./types";

// Default to relative URLs so requests go through the Next.js dev rewrite
// (see next.config.mjs). This keeps the browser on a single origin and
// avoids cross-port cookie issues in Safari/ITP. Override with an absolute
// URL when the frontend is deployed separately from the API.
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");

type ApiOptions = RequestInit & {
  params?: Record<string, string | number | boolean | undefined | null>;
};

function url(path: string, params?: ApiOptions["params"]) {
  // When API_BASE is empty (proxied through Next.js rewrites) we build a
  // relative URL. URLSearchParams handles the query string.
  if (path.startsWith("http")) {
    const endpoint = new URL(path);
    applyParams(endpoint.searchParams, params);
    return endpoint.toString();
  }

  if (!API_BASE) {
    const search = new URLSearchParams();
    applyParams(search, params);
    const qs = search.toString();
    return qs ? `${path}?${qs}` : path;
  }

  const endpoint = new URL(`${API_BASE}${path}`);
  applyParams(endpoint.searchParams, params);
  return endpoint.toString();
}

function applyParams(target: URLSearchParams, params?: ApiOptions["params"]) {
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      target.set(key, String(value));
    }
  });
}

export class ApiError extends Error {
  status: number;
  detail: string;
  requestId?: string;

  constructor(status: number, detail: string, requestId?: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.requestId = requestId;
  }
}

async function request<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  // Per-request correlation id; backend echoes this back so support can trace failures.
  if (!headers.has("X-Request-ID")) headers.set("X-Request-ID", cryptoRandomId());

  const response = await fetch(url(path, options.params), {
    ...options,
    headers,
    // Backend sets the session as an HttpOnly cookie. Cross-origin XHR/fetch
    // omits cookies by default, so we must opt in for every call.
    credentials: "include",
    cache: "no-store"
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.message || detail;
    } catch {
      try {
        detail = (await response.text()) || detail;
      } catch {
        // ignore
      }
    }
    throw new ApiError(response.status, detail, response.headers.get("X-Request-ID") || undefined);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function cryptoRandomId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export const api = {
  baseUrl: API_BASE,

  me: () => request<User>("/api/v1/auth/me"),

  devLogin: (email: string) =>
    request<{ access_token: string; token_type: string; user: User }>("/api/v1/auth/dev-login", {
      method: "POST",
      body: JSON.stringify({ email, name: email.split("@")[0] })
    }),

  logout: () =>
    request<{ message?: string }>("/api/v1/auth/logout", { method: "POST" }).catch((error) => {
      // Logout is best-effort: a 401 just means the cookie was already gone.
      if (error instanceof ApiError && (error.status === 401 || error.status === 302)) return {};
      throw error;
    }),

  // Browser navigates here directly (full page load), so even when API_BASE
  // is empty we hit the rewrite and end up on the backend redirect.
  googleLoginUrl: () => `${API_BASE || ""}/api/v1/auth/google/login`,

  listTasks: (userId?: number) =>
    request<{ tasks: unknown[]; total: number }>("/api/v1/tasks", {
      params: { page_size: 12, user_id: userId || undefined }
    }),

  deleteTask: (taskId: string) =>
    request<{ message: string }>(`/api/v1/tasks/${encodeURIComponent(taskId)}/hard`, { method: "DELETE" }),

  cancelTask: (taskId: string) =>
    request<{ message: string }>(`/api/v1/tasks/${encodeURIComponent(taskId)}`, { method: "DELETE" }),

  patchTask: (taskId: string, action: "cancel" | "hold" | "resume" | "restart") =>
    request<{ message: string }>(`/api/v1/tasks/${encodeURIComponent(taskId)}`, {
      method: "PATCH",
      body: JSON.stringify({ action })
    }),

  getTask: (taskId: string) =>
    request<Record<string, unknown>>(`/api/v1/tasks/${encodeURIComponent(taskId)}`),

  suggest: (query: string) =>
    request<Suggestion>("/api/v1/leaderboard/suggest", {
      method: "POST",
      body: JSON.stringify({ query })
    }),

  recentModels: () => request<{ models: string[] }>("/api/v1/dataset/models/recent"),

  samples: (filters: { language?: string | null; subject_type?: string | null; task_type?: string | null }) =>
    request<{ total: number; samples: DatasetSample[] }>("/api/v1/dataset/sample", {
      params: { ...filters, limit: 5 }
    }),

  startEvaluation: (payload: {
    query: string;
    sample_scale: string;
    models: ModelConfig[];
    category_language?: string | null;
    category_subject?: string | null;
    category_task_type?: string | null;
  }) =>
    request<{ task_id: string; status: string; message: string }>("/api/v1/leaderboard/generate", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  categories: () =>
    request<{ languages: string[]; subject_types: string[]; task_types: string[] }>(
      "/api/v1/leaderboard/categories"
    ),

  leaderboard: (params: { language?: string; subject_type?: string; task_type?: string; limit?: number }) =>
    request<{ entries: LeaderboardEntry[]; query: string; generated_at: string; total_models: number }>(
      "/api/v1/leaderboard/browse",
      { params }
    ),

  managerSnapshot: () => request<ManagerSnapshot>("/api/v1/manager/snapshot"),

  createLeaderboardEntry: (payload: {
    model_name: string;
    language: string;
    subject_type: string;
    task_type: string;
    score: number;
  }) =>
    request<LeaderboardEntry>("/api/v1/leaderboard/entries", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  deleteLeaderboardEntry: (entryId: number) =>
    request<{ message: string }>(`/api/v1/leaderboard/entries/${entryId}`, { method: "DELETE" }),

  // ----- conversational evaluation drafts -----

  createDraft: () =>
    request<EvaluationDraft>("/api/v1/evaluation/drafts", { method: "POST" }),

  listDrafts: (limit = 20) =>
    request<{ drafts: EvaluationDraft[] }>("/api/v1/evaluation/drafts", { params: { limit } }),

  getDraft: (id: number) =>
    request<EvaluationDraft>(`/api/v1/evaluation/drafts/${id}`),

  deleteDraft: (id: number) =>
    request<void>(`/api/v1/evaluation/drafts/${id}`, { method: "DELETE" }),

  sendDraftMessage: (id: number, message: string) =>
    request<EvaluationDraft & { ready?: boolean; rationale?: string | null }>(
      `/api/v1/evaluation/drafts/${id}/messages`,
      { method: "POST", body: JSON.stringify({ message }) }
    ),

  launchDraft: (id: number, models: ModelConfig[]) =>
    request<{ draft_id: number; task_id: string; status: string; message: string }>(
      `/api/v1/evaluation/drafts/${id}/launch`,
      { method: "POST", body: JSON.stringify({ models }) }
    )
};

export function normalizeStatus(status: unknown): TaskSummary["status"] {
  const value = String(status || "").toUpperCase();
  if (value === "SUCCESS" || value === "COMPLETED") return "completed";
  if (value === "STARTED" || value === "PROGRESS" || value === "RUNNING") return "running";
  if (value === "FAILURE" || value === "FAILED" || value === "CANCELLED" || value === "CANCELED") return "failed";
  return "pending";
}

export function formatDate(value: unknown) {
  if (!value) return "-";
  return String(value).slice(0, 19).replace("T", " ");
}

export function taskFromApi(task: Record<string, unknown>): TaskSummary {
  const status = normalizeStatus(task.status);
  return {
    id: String(task.task_id || task.id || ""),
    status,
    progress: status === "completed" ? 100 : status === "running" ? 35 : status === "pending" ? 8 : 0,
    modelName: task.model_count ? `${task.model_count} model(s)` : "Evaluation",
    query: String(task.query || (Array.isArray(task.policy_tags) ? task.policy_tags.join(", ") : "") || "Evaluation task"),
    createdAt: formatDate(task.created_at)
  };
}

export function taskDetailFromApi(taskId: string, payload: Record<string, unknown>): TaskDetail {
  const status = normalizeStatus(payload.status);
  const result = (payload.result || {}) as Record<string, unknown>;
  const storage = (result.storage_stats || {}) as Record<string, unknown>;
  const modelResults = Array.isArray(result.model_results) ? (result.model_results as Record<string, unknown>[]) : [];
  const requestPayload = (payload.request_payload || {}) as Record<string, unknown>;
  const models = Array.isArray(requestPayload.models)
    ? (requestPayload.models as Omit<ModelConfig, "api_key">[])
    : [];
  const stageTotal = Number(payload.stage_total || 1);
  const stagePct = payload.stage
    ? Math.round((Number(payload.stage_current || 0) / Math.max(stageTotal, 1)) * 100)
    : status === "completed"
      ? 100
      : status === "running"
        ? 35
        : 0;

  return {
    id: taskId,
    status,
    createdAt: formatDate(payload.created_at),
    completedAt: formatDate(payload.completed_at),
    stage: String(payload.stage || (status === "completed" ? "Evaluation complete" : status === "failed" ? "Evaluation failed" : "Queued")),
    stagePct,
    errorMessage: String(payload.error_message || ""),
    sampleScale: String(requestPayload.sample_scale || ""),
    models,
    labels: [
      requestPayload.category_language,
      requestPayload.category_subject,
      requestPayload.category_task_type
    ].filter(Boolean).map(String),
    rows: modelResults.map((entry) => {
      const accuracy = entry.accuracy;
      return {
        modelName: String(entry.model_name || "-"),
        accuracy: typeof accuracy === "number" ? `${(accuracy * 100).toFixed(1)}%` : "-",
        samples: String(storage.samples_stored || entry.total_samples || "-"),
        executionTime: entry.execution_time ? `${Number(entry.execution_time).toFixed(0)}s` : "-"
      };
    })
  };
}
