export type User = {
  id: number;
  email: string;
  name?: string | null;
  picture?: string | null;
  role?: string | null;
};

export type ModelConfig = {
  name: string;
  api_base: string;
  api_key: string;
  model_type: "openai" | "anthropic" | "huggingface" | "custom";
};

export type TaskSummary = {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  modelName: string;
  query: string;
  createdAt: string;
};

export type Suggestion = {
  query: string;
  language?: string | null;
  subject_type?: string | null;
  task_type?: string | null;
  subject_type_options?: string[];
  plan_summary: string;
  used_planner?: boolean;
  confidence?: number;
  rationale?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type DatasetSample = {
  id?: number;
  benchmark_name?: string;
  language?: string;
  subject_type?: string;
  task_type?: string;
  problem_type?: string;
  prompt?: string;
  options?: string;
  answer_str?: string;
};

export type LeaderboardEntry = {
  id?: number;
  model_name: string;
  language: string;
  subject_type: string;
  task_type: string;
  score: number;
  last_updated: string;
  quarantined?: boolean;
};

export type TaskResultRow = {
  modelName: string;
  accuracy: string;
  samples: string;
  executionTime: string;
};

export type TaskDetail = {
  id: string;
  status: TaskSummary["status"];
  createdAt: string;
  completedAt: string;
  stage: string;
  stagePct: number;
  errorMessage: string;
  rows: TaskResultRow[];
  models: Omit<ModelConfig, "api_key">[];
  sampleScale: string;
  labels: string[];
};

export type EvaluationSpec = {
  query?: string;
  category_language?: string;
  category_subject?: string;
  category_task_type?: string;
  sample_scale?: string;
  suggested_models?: Array<{
    name: string;
    model_type?: ModelConfig["model_type"];
    api_base?: string;
    note?: string;
  }>;
};

export type ChatLookup = {
  filters: Record<string, unknown>;
  entries: LeaderboardEntry[];
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
  rationale?: string | null;
  lookups?: ChatLookup[];
};

export type EvaluationDraft = {
  id: number;
  title?: string | null;
  status: "draft" | "launched" | "abandoned";
  spec: EvaluationSpec;
  messages: ChatMessage[];
  missing_slots: string[];
  launched_task_id?: string | null;
  created_at?: string;
  updated_at?: string | null;
};

export type ManagerSnapshot = {
  timestamp: string;
  health: Record<string, { status: string; name?: string }>;
  capacity: Record<string, number>;
  tasks: Array<{
    task_id: string;
    status: string;
    submitted_at: string;
    completed_at?: string | null;
    duration_seconds?: number | null;
    model_count?: number | null;
    query?: string | null;
  }>;
  leaderboard: LeaderboardEntry[];
  planner_available: boolean;
  hret_available: boolean;
};
