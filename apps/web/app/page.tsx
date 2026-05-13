"use client";

import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import {
  Activity,
  BarChart3,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Database,
  Github,
  Loader2,
  LogIn,
  LogOut,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Pause,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Server,
  Settings,
  ShieldCheck,
  Sparkles,
  SquarePen,
  Trash2,
  Trophy,
  X
} from "lucide-react";
import { ApiError, api, formatDate, normalizeStatus, taskDetailFromApi, taskFromApi } from "@/services/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import EvaluationChatView from "./_components/EvaluationChatView";
import { ThemeToggle } from "./_components/ThemeToggle";
import type {
  EvaluationDraft,
  LeaderboardEntry,
  ManagerSnapshot,
  Suggestion,
  TaskDetail,
  TaskSummary,
  User
} from "@/services/types";

const SAMPLE_OPTIONS = [
  { id: "small", label: "Small", meta: "50 samples" },
  { id: "medium", label: "Medium", meta: "100 samples" },
  { id: "large", label: "Large", meta: "250 samples" },
  { id: "full", label: "Full", meta: "500 samples" }
];

type View = "evaluation" | "leaderboard" | "manager";
type EvalStep = "input" | "detail";

function isOffTopic(suggestion: Suggestion | null) {
  return suggestion?.metadata?.reason === "off_topic";
}

function sampleLabel(scale: string) {
  const preset = SAMPLE_OPTIONS.find((option) => option.id === scale);
  if (preset) return `${preset.label} (${preset.meta})`;
  if (scale.startsWith("custom:")) return `Custom (${scale.replace("custom:", "")})`;
  return scale || "Medium (100 samples)";
}

function scoreLabel(score: number) {
  return Number.isFinite(score) ? score.toFixed(2) : "-";
}

// Dev login is gated behind a build-time check. Production bundles ship
// without the form so no one is tempted by it; the backend also refuses the
// route unless DEBUG=true. Set NEXT_PUBLIC_ENABLE_DEV_ACCESS=1 to force it
// on for staging-style preview builds.
const SHOW_DEV_ACCESS =
  process.env.NODE_ENV !== "production" ||
  process.env.NEXT_PUBLIC_ENABLE_DEV_ACCESS === "1";

export default function BenchHubApp() {
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [authError, setAuthError] = useState("");
  const [devEmail, setDevEmail] = useState("dev@local");

  const [view, setView] = useState<View>("evaluation");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskDetail | null>(null);
  const [drafts, setDrafts] = useState<EvaluationDraft[]>([]);
  const [activeDraftId, setActiveDraftId] = useState<number | null>(null);

  const [evalStep, setEvalStep] = useState<EvalStep>("input");

  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [leaderboardQuery, setLeaderboardQuery] = useState("");
  const [leaderboardSuggestion, setLeaderboardSuggestion] = useState<Suggestion | null>(null);
  const [categories, setCategories] = useState({ languages: ["All"], subjects: ["All"], tasks: ["All"] });
  const [filters, setFilters] = useState({ language: "All", subject: "All", taskType: "All", limit: 100 });

  const [manager, setManager] = useState<ManagerSnapshot | null>(null);
  const [newEntry, setNewEntry] = useState({ model: "", language: "", subject: "", taskType: "", score: "" });

  const [loading, setLoading] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ tone: "success" | "error" | "info"; text: string } | null>(null);

  const isAuthed = Boolean(user);
  const isAdmin = user?.role === "admin";
  const activeTaskCount = tasks.filter((task) => task.status === "running" || task.status === "pending").length;
  const completedTaskCount = tasks.filter((task) => task.status === "completed").length;

  function show(tone: "success" | "error" | "info", text: string) {
    setNotice({ tone, text });
    window.setTimeout(() => setNotice(null), 4200);
  }

  function handleApiError(error: unknown, fallback: string): string {
    if (error instanceof ApiError && error.status === 401) {
      // Session expired — drop UI auth state so the user is bounced to login.
      setUser(null);
      setTasks([]);
      setSelectedTask(null);
      setDrafts([]);
      setActiveDraftId(null);
      return "Your session has expired. Please sign in again.";
    }
    return error instanceof Error ? error.message : fallback;
  }

  async function loadSession() {
    setLoading("auth");
    try {
      const nextUser = await api.me();
      setUser(nextUser);
      setAuthError("");
      await Promise.all([
        loadTasks(nextUser.id),
        loadDrafts(),
        loadCategories(),
        loadLeaderboard()
      ]);
    } catch (error) {
      setUser(null);
      // 401 just means no/expired session — don't surface as an error message.
      const message = error instanceof Error ? error.message : "";
      if (message && !/not authenticated|401/i.test(message)) {
        setAuthError(message);
      } else {
        setAuthError("");
      }
    } finally {
      setAuthChecked(true);
      setLoading(null);
    }
  }

  async function loadTasks(userId = user?.id) {
    if (!user && userId === undefined) return;
    const payload = await api.listTasks(userId);
    setTasks(payload.tasks.map((task) => taskFromApi(task as Record<string, unknown>)));
  }

  async function loadDrafts() {
    try {
      const payload = await api.listDrafts(20);
      const ongoing = (payload.drafts || []).filter((d) => d.status === "draft");
      setDrafts(ongoing);
    } catch {
      // History is best-effort; don't surface failures here.
    }
  }

  // Called by EvaluationChatView whenever its draft state changes so the
  // sidebar reflects new conversations immediately (no extra round-trip).
  // Memoized so the child effect that calls it doesn't re-fire each render.
  const handleDraftSync = useCallback((draft: EvaluationDraft | null) => {
    if (!draft) return;
    if (draft.status !== "draft") {
      setDrafts((current) => current.filter((d) => d.id !== draft.id));
      setActiveDraftId((current) => (current === draft.id ? null : current));
      return;
    }
    // Update in place if the draft already exists so clicking an older entry
    // doesn't yank it to the top (keeps the gray "selected" indicator on the
    // row the user actually clicked). New drafts get prepended.
    setDrafts((current) => {
      const idx = current.findIndex((d) => d.id === draft.id);
      if (idx >= 0) {
        const next = current.slice();
        next[idx] = draft;
        return next;
      }
      return [draft, ...current];
    });
    setActiveDraftId(draft.id);
  }, []);

  async function openDraft(draftId: number) {
    setView("evaluation");
    setEvalStep("input");
    setSelectedTask(null);
    setActiveDraftId(draftId);
  }

  async function forkSourceDraft(sourceDraftId: number) {
    if (!isAuthed) return;
    setLoading("draft-fork");
    try {
      const cloned = await api.forkDraft(sourceDraftId);
      setDrafts((current) => {
        const next = current.filter((d) => d.id !== cloned.id);
        return [cloned, ...next];
      });
      setSelectedTask(null);
      setView("evaluation");
      setEvalStep("input");
      setActiveDraftId(cloned.id);
      show("success", "Thread forked. Edit and run as a new evaluation.");
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to fork thread");
    } finally {
      setLoading(null);
    }
  }

  async function removeDraft(draftId: number) {
    setDrafts((current) => current.filter((d) => d.id !== draftId));
    if (activeDraftId === draftId) setActiveDraftId(null);
    if (!isAuthed) return;
    try {
      await api.deleteDraft(draftId);
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to delete draft");
    }
  }

  async function loadCategories() {
    try {
      const payload = await api.categories();
      setCategories({
        languages: ["All", ...new Set((payload.languages || []).filter(Boolean))],
        subjects: ["All", ...new Set((payload.subject_types || []).filter(Boolean))],
        tasks: ["All", ...new Set((payload.task_types || []).filter(Boolean))]
      });
    } catch {
      setCategories({ languages: ["All"], subjects: ["All"], tasks: ["All"] });
    }
  }

  async function loadLeaderboard(nextFilters = filters) {
    setLoading("leaderboard");
    try {
      const payload = await api.leaderboard({
        language: nextFilters.language === "All" ? undefined : nextFilters.language,
        subject_type: nextFilters.subject === "All" ? undefined : nextFilters.subject,
        task_type: nextFilters.taskType === "All" ? undefined : nextFilters.taskType,
        limit: nextFilters.limit
      });
      setLeaderboard(payload.entries || []);
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to load leaderboard");
    } finally {
      setLoading(null);
    }
  }

  useEffect(() => {
    // The browser may still carry the legacy `?token=...` query string from
    // pre-cookie deployments. Strip it so the URL stays clean; the session
    // itself comes from the HttpOnly cookie set by the backend.
    const params = new URLSearchParams(window.location.search);
    if (params.has("token")) {
      params.delete("token");
      const next = params.toString();
      window.history.replaceState(
        {},
        document.title,
        window.location.pathname + (next ? `?${next}` : "")
      );
    }
    // Drop any token left behind by older builds.
    try {
      window.localStorage.removeItem("benchhub.token");
    } catch {
      /* ignore */
    }
    void loadSession();
    // Session bootstrap runs once against the cookie set by the backend.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!isAuthed || !selectedTask || selectedTask.status === "completed" || selectedTask.status === "failed") return;
    // Add jitter so multiple clients don't sync up on the backend.
    const delay = 5000 + Math.floor(Math.random() * 1500);
    const timer = window.setInterval(() => {
      void refreshTask(selectedTask.id, false);
    }, delay);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthed, selectedTask?.id, selectedTask?.status]);

  useEffect(() => {
    if (!isAuthed || view !== "manager") return;
    void refreshManager();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthed, view]);

  async function devLogin() {
    setLoading("auth");
    try {
      // The backend sets the auth cookie on the dev-login response; the
      // returned access_token is informational only.
      await api.devLogin(devEmail);
      await loadSession();
      show("success", "Signed in with development account");
    } catch (error) {
      if (process.env.NEXT_PUBLIC_DEV_OFFLINE === "true") {
        const fakeUser: User = {
          id: 0,
          email: devEmail || "dev@local",
          name: (devEmail || "dev@local").split("@")[0],
          picture: null,
          role: "admin"
        };
        setUser(fakeUser);
        setAuthError("");
        setAuthChecked(true);
        try {
          await Promise.all([loadCategories(), loadLeaderboard()]);
        } catch {
          /* offline: ignore data-fetch errors */
        }
        show("info", `Offline UI preview as ${fakeUser.email} (backend unreachable)`);
        return;
      }
      show("error", error instanceof Error ? error.message : "Development login failed");
    } finally {
      setLoading(null);
    }
  }

  async function logout() {
    setLoading("auth");
    try {
      await api.logout();
    } catch {
      // best-effort; backend may already have invalidated the cookie
    } finally {
      setUser(null);
      setTasks([]);
      setDrafts([]);
      setActiveDraftId(null);
      setSelectedTask(null);
      try {
        window.localStorage.removeItem("benchhub.token");
      } catch {
        /* ignore */
      }
      setLoading(null);
    }
  }

  async function refreshTask(taskId: string, notify = true) {
    if (!isAuthed || taskId.startsWith("pending-")) return;
    try {
      const payload = await api.getTask(taskId);
      const detail = taskDetailFromApi(taskId, payload);
      setSelectedTask(detail);
      setTasks((current) =>
        current.map((task) =>
          task.id === taskId
            ? {
                ...task,
                status: detail.status,
                progress: detail.stagePct,
                createdAt: detail.createdAt
              }
            : task
        )
      );
      if (notify) show("success", "Task refreshed");
    } catch (error) {
      if (notify) show("error", error instanceof Error ? error.message : "Failed to refresh task");
    }
  }

  async function openTask(taskId: string) {
    setView("evaluation");
    setEvalStep("detail");
    setActiveDraftId(null);
    if (taskId.startsWith("pending-")) {
      setSelectedTask(null);
      return;
    }
    setLoading("task");
    await refreshTask(taskId, false);
    setLoading(null);
  }

  async function removeTask(taskId: string) {
    setTasks((current) => current.filter((task) => task.id !== taskId));
    if (selectedTask?.id === taskId) setSelectedTask(null);
    if (!isAuthed || taskId.startsWith("pending-")) return;
    try {
      await api.deleteTask(taskId);
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to delete task");
    }
  }

  async function cancelSelectedTask() {
    if (!isAuthed || !selectedTask) return;
    setLoading("task-action");
    try {
      await api.cancelTask(selectedTask.id);
      await refreshTask(selectedTask.id, false);
      show("success", "Task cancelled");
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to cancel task");
    } finally {
      setLoading(null);
    }
  }

  async function restartSelectedTask() {
    if (!isAuthed || !selectedTask) return;
    setLoading("task-action");
    try {
      await api.patchTask(selectedTask.id, "restart");
      await refreshTask(selectedTask.id, false);
      show("success", "Restart requested");
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to restart task");
    } finally {
      setLoading(null);
    }
  }

  async function suggestLeaderboard() {
    if (!isAuthed || !leaderboardQuery.trim()) return;
    setLoading("leaderboard-suggest");
    try {
      const payload = await api.suggest(leaderboardQuery.trim());
      setLeaderboardSuggestion(payload);
      if (payload.language || payload.subject_type || payload.task_type) {
        const nextFilters = {
          ...filters,
          language: payload.language || "All",
          subject: payload.subject_type || "All",
          taskType: payload.task_type || "All"
        };
        setFilters(nextFilters);
        if (!isOffTopic(payload)) await loadLeaderboard(nextFilters);
      }
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Search planning failed");
    } finally {
      setLoading(null);
    }
  }

  async function refreshManager() {
    if (!isAuthed) return;
    setLoading("manager");
    try {
      const payload = await api.managerSnapshot();
      setManager(payload);
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to load manager snapshot");
    } finally {
      setLoading(null);
    }
  }

  async function patchManagerTask(taskId: string, action: "cancel" | "hold" | "resume" | "restart") {
    if (!isAuthed) return;
    setLoading("manager");
    try {
      await api.patchTask(taskId, action);
      await refreshManager();
      show("success", `Task ${action} requested`);
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Task update failed");
    } finally {
      setLoading(null);
    }
  }

  async function addLeaderboardEntry() {
    if (!isAuthed) return;
    const score = Number(newEntry.score);
    if (!newEntry.model.trim() || !Number.isFinite(score)) return show("error", "Model and numeric score are required");
    setLoading("manager");
    try {
      await api.createLeaderboardEntry({
        model_name: newEntry.model,
        language: newEntry.language,
        subject_type: newEntry.subject,
        task_type: newEntry.taskType,
        score
      });
      setNewEntry({ model: "", language: "", subject: "", taskType: "", score: "" });
      await refreshManager();
      show("success", "Leaderboard entry saved");
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to save entry");
    } finally {
      setLoading(null);
    }
  }

  async function removeLeaderboardEntry(entryId?: number) {
    if (!isAuthed || !entryId) return;
    setLoading("manager");
    try {
      await api.deleteLeaderboardEntry(entryId);
      await refreshManager();
      show("success", "Leaderboard entry removed");
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to remove entry");
    } finally {
      setLoading(null);
    }
  }

  async function approveLeaderboardEntry(entryId?: number) {
    if (!isAuthed || !entryId) return;
    setLoading("manager");
    try {
      await api.approveLeaderboardEntry(entryId);
      await refreshManager();
      show("success", "Leaderboard entry approved");
    } catch (error) {
      show("error", error instanceof Error ? error.message : "Failed to approve entry");
    } finally {
      setLoading(null);
    }
  }

  function newEvaluation() {
    setView("evaluation");
    setEvalStep("input");
    setSelectedTask(null);
    setActiveDraftId(null);
  }

  if (!authChecked) {
    return (
      <main
        className="flex min-h-screen items-center justify-center bg-background"
        aria-busy="true"
        aria-live="polite"
      >
        <Loader2 className="size-7 animate-spin text-muted-foreground" aria-label="Loading session" />
      </main>
    );
  }

  if (!isAuthed) {
    return (
      <main className="relative flex min-h-screen items-center justify-center bg-background px-6">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 [background:radial-gradient(60%_60%_at_50%_-10%,hsl(var(--accent)/0.08)_0%,transparent_60%)]"
        />
        <section
          className="relative w-full max-w-md animate-fade-in"
          aria-labelledby="auth-heading"
        >
          <div className="mb-8 flex items-center gap-2 text-sm">
            <span className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground">
              <Trophy size={14} aria-hidden="true" />
            </span>
            <span className="font-medium tracking-tight">BenchHub Plus</span>
          </div>

          <h1
            id="auth-heading"
            className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl"
          >
            LLM evaluation operations,
            <br />
            <span className="text-muted-foreground">ready for launch.</span>
          </h1>
          <p className="mt-3 text-sm text-muted-foreground">
            Plan benchmark scope, run model comparisons, and govern leaderboard quality from one workspace.
          </p>

          <form
            className="mt-8 space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              void devLogin();
            }}
          >
            <a
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              href={api.githubLoginUrl()}
            >
              <Github size={16} aria-hidden="true" />
              Continue with GitHub
            </a>

            {SHOW_DEV_ACCESS ? (
              <>
                <div className="relative my-1 text-center text-xs text-muted-foreground">
                  <span className="bg-background px-2 relative z-10">or use dev access</span>
                  <span className="absolute left-0 right-0 top-1/2 -z-0 h-px -translate-y-1/2 bg-border" />
                </div>

                <div className="flex gap-2">
                  <label className="sr-only" htmlFor="dev-email">
                    Development email
                  </label>
                  <input
                    id="dev-email"
                    type="email"
                    inputMode="email"
                    autoComplete="email"
                    placeholder="dev@local"
                    value={devEmail}
                    onChange={(event) => setDevEmail(event.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                  <button
                    type="submit"
                    className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-input bg-background px-4 text-sm font-medium shadow-sm transition-colors hover:bg-secondary disabled:pointer-events-none disabled:opacity-50"
                    disabled={loading === "auth" || !devEmail.trim()}
                  >
                    {loading === "auth" ? (
                      <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                    ) : (
                      <Github size={16} aria-hidden="true" />
                    )}
                    Dev
                  </button>
                </div>
              </>
            ) : null}
          </form>
          {authError ? (
            <p
              className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
              role="alert"
            >
              {authError}
            </p>
          ) : null}
          <p className="mt-8 text-center text-xs text-muted-foreground">
            By continuing you agree to BenchHub Plus terms.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="grid min-h-screen grid-cols-1 bg-background md:grid-cols-[260px_minmax(0,1fr)]">
      <aside
        className={clsx(
          "flex flex-col gap-1 border-b border-border bg-card md:h-screen md:border-b-0 md:border-r md:sticky md:top-0",
          sidebarCollapsed && "md:!w-[64px]"
        )}
        aria-label="Primary navigation"
      >
        <div className="flex items-center justify-between gap-2 px-4 py-4">
          {!sidebarCollapsed ? (
            <div className="flex items-center gap-2 text-sm font-medium tracking-tight">
              <span className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground">
                <Trophy size={14} aria-hidden="true" />
              </span>
              <span>BenchHub Plus</span>
            </div>
          ) : (
            <span className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground">
              <Trophy size={14} aria-hidden="true" />
            </span>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="hidden md:inline-flex"
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!sidebarCollapsed}
            onClick={() => setSidebarCollapsed((value) => !value)}
          >
            {sidebarCollapsed ? <PanelLeftOpen aria-hidden="true" /> : <PanelLeftClose aria-hidden="true" />}
          </Button>
        </div>

        <nav className="flex flex-row gap-1 px-3 md:flex-col" aria-label="Workspace sections">
          <NavItem
            label="Leaderboard"
            icon={<Trophy />}
            active={view === "leaderboard"}
            collapsed={sidebarCollapsed}
            onClick={() => setView("leaderboard")}
          />
          <NavItem
            label="New Evaluation"
            icon={<SquarePen />}
            active={view === "evaluation" && evalStep !== "detail"}
            collapsed={sidebarCollapsed}
            onClick={newEvaluation}
          />
          {isAdmin ? (
            <NavItem
              label="Manager"
              icon={<Settings />}
              active={view === "manager"}
              collapsed={sidebarCollapsed}
              onClick={() => setView("manager")}
            />
          ) : null}
        </nav>

        {!sidebarCollapsed ? (
          <div className="hidden min-h-0 flex-1 flex-col gap-2 px-3 py-4 md:flex">
            <div className="flex items-center justify-between px-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              <span>History</span>
              <Button
                variant="ghost"
                size="icon"
                className="size-6"
                title="Refresh history"
                onClick={() => {
                  void loadTasks();
                  void loadDrafts();
                }}
              >
                <RefreshCw className="size-3.5" aria-hidden="true" />
              </Button>
            </div>
            <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto pr-1">
              {drafts.length === 0 && tasks.length === 0 ? (
                <p className="px-2 py-6 text-center text-xs text-muted-foreground">
                  No evaluations yet
                </p>
              ) : null}

              {drafts.map((draft) => {
                const lastUserMessage = [...draft.messages]
                  .reverse()
                  .find((m) => m.role === "user")?.content;
                const label =
                  draft.title?.trim() ||
                  draft.spec.query?.trim() ||
                  lastUserMessage?.trim() ||
                  "New conversation";
                const isActive = activeDraftId === draft.id;
                const subtitle =
                  draft.messages.length > 0
                    ? `Draft · ${draft.messages.length} message${draft.messages.length === 1 ? "" : "s"}`
                    : "Draft · just started";
                return (
                  <button
                    key={`draft-${draft.id}`}
                    type="button"
                    onClick={() => void openDraft(draft.id)}
                    className={clsx(
                      "group flex items-start gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors hover:bg-secondary",
                      isActive && "bg-secondary"
                    )}
                  >
                    <MessageSquare
                      className="mt-0.5 size-3.5 shrink-0 text-accent"
                      aria-hidden="true"
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{label}</span>
                      <span className="block truncate text-[11px] text-muted-foreground">
                        {subtitle}
                      </span>
                    </span>
                    <button
                      type="button"
                      className="shrink-0 rounded-md p-1 text-muted-foreground opacity-0 transition group-hover:opacity-100 hover:bg-card hover:text-foreground"
                      aria-label={`Remove draft ${label}`}
                      onClick={(event) => {
                        event.stopPropagation();
                        void removeDraft(draft.id);
                      }}
                    >
                      <X className="size-3" aria-hidden="true" />
                    </button>
                  </button>
                );
              })}

              {tasks.map((task) => {
                const isTaskActive =
                  view === "evaluation" &&
                  evalStep === "detail" &&
                  selectedTask?.id === task.id;
                return (
                <button
                  key={task.id}
                  type="button"
                  onClick={() => void openTask(task.id)}
                  className={clsx(
                    "group flex items-start gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors hover:bg-secondary",
                    isTaskActive && "bg-secondary"
                  )}
                >
                  <span
                    className={clsx(
                      "mt-1.5 size-1.5 shrink-0 rounded-full",
                      task.status === "running" && "bg-amber-500 animate-pulse",
                      task.status === "completed" && "bg-emerald-500",
                      task.status === "failed" && "bg-destructive",
                      task.status === "pending" && "bg-muted-foreground/40"
                    )}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{task.query}</span>
                    <span className="block truncate text-[11px] text-muted-foreground">
                      {task.createdAt} · {task.modelName}
                    </span>
                  </span>
                  <button
                    type="button"
                    className="shrink-0 rounded-md p-1 text-muted-foreground opacity-0 transition group-hover:opacity-100 hover:bg-card hover:text-foreground"
                    aria-label={`Remove ${task.query}`}
                    onClick={(event) => {
                      event.stopPropagation();
                      void removeTask(task.id);
                    }}
                  >
                    <X className="size-3" aria-hidden="true" />
                  </button>
                </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </aside>

      <section className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-border bg-background/80 px-6 py-3 backdrop-blur">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <StatPill icon={<Activity className="size-3.5" />} label="Active" value={activeTaskCount} accent={activeTaskCount > 0} />
            <StatPill icon={<CheckCircle2 className="size-3.5" />} label="Complete" value={completedTaskCount} />
            <StatPill icon={<Database className="size-3.5" />} label="Leaderboard" value={leaderboard.length} />
          </div>
          <div className="flex items-center gap-1">
            <span className="hidden truncate text-xs text-muted-foreground sm:inline-block sm:max-w-[180px]">
              {user?.name || user?.email}
            </span>
            <ThemeToggle />
            <Button
              variant="ghost"
              size="icon"
              title="Log out"
              aria-label="Log out"
              onClick={logout}
            >
              <LogOut className="size-4" />
            </Button>
          </div>
        </header>

        <div className="flex-1 px-6 py-6">
        {authError ? <Banner tone="error" text={authError} /> : null}
        {notice ? <Banner tone={notice.tone} text={notice.text} /> : null}

        {view === "evaluation" ? (
          evalStep === "detail" && selectedTask ? (
            <EvaluationView
              loading={loading}
              selectedTask={selectedTask}
              refreshTask={refreshTask}
              cancelSelectedTask={cancelSelectedTask}
              restartSelectedTask={restartSelectedTask}
              isAdmin={isAdmin}
              onBackToThread={(draftId) => {
                setActiveDraftId(draftId);
                setSelectedTask(null);
                setEvalStep("input");
              }}
              onForkThread={forkSourceDraft}
              setEvalStep={setEvalStep}
            />
          ) : (
            <EvaluationChatView
              activeDraftId={activeDraftId}
              onDraftChanged={handleDraftSync}
              onFork={forkSourceDraft}
              onLaunched={async (taskId) => {
                show("success", "Evaluation queued");
                setEvalStep("detail");
                setActiveDraftId(null);
                await refreshTask(taskId, false);
                await Promise.all([loadTasks(), loadDrafts()]);
              }}
              onError={(message) => show("error", message)}
            />
          )
        ) : null}

        {view === "leaderboard" ? (
          <LeaderboardView
            loading={loading}
            query={leaderboardQuery}
            setQuery={setLeaderboardQuery}
            suggestion={leaderboardSuggestion}
            suggest={suggestLeaderboard}
            categories={categories}
            filters={filters}
            setFilters={setFilters}
            load={() => void loadLeaderboard()}
            rows={leaderboard}
          />
        ) : null}

        {view === "manager" ? (
          <ManagerView
            loading={loading}
            snapshot={manager}
            refresh={refreshManager}
            patchTask={patchManagerTask}
            entry={newEntry}
            setEntry={setNewEntry}
            addEntry={addLeaderboardEntry}
            removeEntry={removeLeaderboardEntry}
            approveEntry={approveLeaderboardEntry}
          />
        ) : null}
        </div>
      </section>
    </main>
  );
}

function NavItem({
  label,
  icon,
  active,
  collapsed,
  onClick
}: {
  label: string;
  icon: React.ReactNode;
  active: boolean;
  collapsed: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={collapsed ? label : undefined}
      aria-current={active ? "page" : undefined}
      className={clsx(
        "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors [&_svg]:size-4 [&_svg]:shrink-0",
        active
          ? "bg-secondary text-foreground"
          : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
        collapsed && "justify-center px-2"
      )}
    >
      {icon}
      {!collapsed ? <span>{label}</span> : null}
    </button>
  );
}

function StatPill({
  icon,
  label,
  value,
  accent
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  accent?: boolean;
}) {
  return (
    <div
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-xs",
        accent ? "border-foreground/20 bg-secondary text-foreground" : "bg-card text-muted-foreground"
      )}
    >
      <span className={accent ? "text-foreground" : "text-muted-foreground"}>{icon}</span>
      <span>{label}</span>
      <span className="ml-1 font-semibold tabular-nums text-foreground">{value}</span>
    </div>
  );
}

function Banner({ tone, text }: { tone: "success" | "error" | "info"; text: string }) {
  const isError = tone === "error";
  return (
    <div
      role={isError ? "alert" : "status"}
      aria-live={isError ? "assertive" : "polite"}
      className={clsx(
        "mb-4 flex items-center gap-2 rounded-lg border px-3 py-2 text-sm animate-fade-in",
        isError
          ? "border-destructive/30 bg-destructive/10 text-destructive"
          : tone === "success"
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
            : "border-border bg-secondary text-foreground"
      )}
    >
      {isError ? <CircleAlert className="size-4 shrink-0" aria-hidden /> : <CheckCircle2 className="size-4 shrink-0" aria-hidden />}
      <span>{text}</span>
    </div>
  );
}

function EvaluationView(props: {
  loading: string | null;
  selectedTask: TaskDetail | null;
  refreshTask: (taskId: string) => Promise<void>;
  cancelSelectedTask: () => Promise<void>;
  restartSelectedTask: () => Promise<void>;
  isAdmin: boolean;
  onBackToThread: (draftId: number | null) => void;
  onForkThread: (draftId: number) => void | Promise<void>;
  setEvalStep: (step: EvalStep) => void;
}) {
  const draftId = props.selectedTask?.draftId ?? null;
  return (
    <TaskDetailPanel
      task={props.selectedTask}
      loading={props.loading}
      refreshTask={props.refreshTask}
      cancelSelectedTask={props.cancelSelectedTask}
      restartSelectedTask={props.restartSelectedTask}
      isAdmin={props.isAdmin}
      onForkThread={props.onForkThread}
      back={() =>
        draftId != null ? props.onBackToThread(draftId) : props.setEvalStep("input")
      }
    />
  );
}


const STUCK_PENDING_THRESHOLD_MS = 60_000;

function parseTaskCreatedAt(task: TaskDetail): number | null {
  const raw = task.createdAtIso || task.createdAt;
  if (!raw) return null;
  let normalized = raw.trim();
  if (!normalized) return null;
  if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(normalized)) {
    normalized = `${normalized.replace(" ", "T")}Z`;
  }
  const millis = Date.parse(normalized);
  return Number.isFinite(millis) ? millis : null;
}

function formatElapsed(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1_000));
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes < 60) return `${minutes}m ${seconds}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

function TaskDetailPanel({
  task,
  loading,
  refreshTask,
  cancelSelectedTask,
  restartSelectedTask,
  isAdmin,
  onForkThread,
  back
}: {
  task: TaskDetail | null;
  loading: string | null;
  refreshTask: (taskId: string) => Promise<void>;
  cancelSelectedTask: () => Promise<void>;
  restartSelectedTask: () => Promise<void>;
  isAdmin: boolean;
  onForkThread: (draftId: number) => void | Promise<void>;
  back: () => void;
}) {
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (task?.status !== "pending") return;
    const id = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => window.clearInterval(id);
  }, [task?.status]);

  if (!task) {
    return (
      <div className="grid min-h-[40vh] place-items-center" aria-busy>
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const statusTone =
    task.status === "completed" ? "success" :
    task.status === "failed" ? "destructive" :
    task.status === "running" ? "accent" : "secondary";

  const isInflight = task.status === "running" || task.status === "pending";
  const canRestart = isAdmin && (task.status === "failed" || task.status === "pending" || task.status === "completed");

  const createdAtMs = parseTaskCreatedAt(task);
  const pendingForMs = task.status === "pending" && createdAtMs !== null ? Math.max(0, now - createdAtMs) : 0;
  const isStuck = task.status === "pending" && pendingForMs >= STUCK_PENDING_THRESHOLD_MS;
  const stuckLabel = formatElapsed(pendingForMs);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex items-start gap-3">
          <Button variant="ghost" size="sm" onClick={back}>
            <ChevronLeft />
            {task.draftId != null ? "Thread" : "Evaluations"}
          </Button>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              Task {task.id.slice(0, 12)}
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">{task.stage}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => void refreshTask(task.id)} disabled={loading === "task"}>
            {loading === "task" ? <Loader2 className="animate-spin" /> : <RefreshCw />}
            Refresh
          </Button>
          {task.draftId != null ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => void onForkThread(task.draftId as number)}
              disabled={loading === "draft-fork"}
              title="Clone this thread into a new editable draft"
            >
              {loading === "draft-fork" ? <Loader2 className="animate-spin" /> : <SquarePen />}
              Edit & fork
            </Button>
          ) : null}
          {canRestart ? (
            <Button variant="outline" size="sm" onClick={() => void restartSelectedTask()} disabled={loading === "task-action"}>
              <RotateCcw />
              Restart
            </Button>
          ) : null}
          {isInflight ? (
            <Button variant="destructive" size="sm" onClick={() => void cancelSelectedTask()} disabled={loading === "task-action"}>
              <Pause />
              Cancel
            </Button>
          ) : null}
        </div>
      </header>

      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge variant={statusTone}>{task.status}</Badge>
            {task.status === "pending" && createdAtMs !== null ? (
              <span
                className={clsx(
                  "font-mono text-[11px] tabular-nums",
                  isStuck ? "text-amber-600 dark:text-amber-400" : "text-muted-foreground"
                )}
                title={`Queued ${stuckLabel} ago`}
                aria-live="polite"
              >
                queued {stuckLabel}
              </span>
            ) : null}
          </div>
          <span className="flex items-center gap-2 font-mono text-xs tabular-nums text-muted-foreground">
            {isInflight && task.stageTotal > 1 ? (
              <span aria-label="Sample progress">
                {task.stageCurrent.toLocaleString()}/{task.stageTotal.toLocaleString()}
              </span>
            ) : null}
            <span>{task.stagePct}%</span>
          </span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className={clsx(
              "h-full rounded-full transition-all",
              task.status === "failed" ? "bg-destructive" :
              task.status === "completed" ? "bg-emerald-500" : "bg-foreground",
              isInflight && "animate-pulse"
            )}
            style={{ width: `${Math.max(4, Math.min(task.stagePct, 100))}%` }}
          />
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline">{sampleLabel(task.sampleScale)}</Badge>
          {task.labels.map((label) => (
            <Badge key={label} variant="secondary">{label}</Badge>
          ))}
        </div>
      </Card>

      {isStuck ? (
        <div
          role="status"
          aria-live="polite"
          className="flex items-start gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-900 dark:text-amber-200"
        >
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          <div className="min-w-0 flex-1 space-y-1">
            <p className="font-medium">Still queued after {stuckLabel}.</p>
            <p className="text-xs text-amber-900/80 dark:text-amber-200/80">
              The evaluation worker may be offline. Try Restart, or ask an admin to bring the worker back up.
            </p>
          </div>
        </div>
      ) : null}

      {task.status === "failed" && (task.errorMessage || task.errorLog) ? (
        <div
          role="alert"
          aria-live="assertive"
          className="rounded-lg border border-destructive/30 bg-destructive/10 text-destructive"
        >
          <div className="flex items-start gap-3 px-4 py-3">
            <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
            <div className="min-w-0 flex-1 space-y-1">
              <p className="text-sm font-medium">Evaluation failed</p>
              <p className="break-words text-sm">
                {task.errorMessage || "No error message was recorded."}
              </p>
              {task.errorLog ? (
                <button
                  type="button"
                  onClick={() => setShowErrorDetails((v) => !v)}
                  className="inline-flex items-center gap-1 text-xs font-medium underline-offset-2 hover:underline"
                  aria-expanded={showErrorDetails}
                >
                  {showErrorDetails ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
                  {showErrorDetails ? "Hide details" : "Show details"}
                </button>
              ) : null}
            </div>
          </div>
          {showErrorDetails && task.errorLog ? (
            <pre className="max-h-72 overflow-auto border-t border-destructive/20 bg-destructive/5 px-4 py-3 font-mono text-[11px] leading-relaxed text-destructive/90 whitespace-pre-wrap break-words">
              {task.errorLog}
            </pre>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
        <Card className="overflow-hidden">
          <div className="flex items-center gap-2 border-b border-border bg-secondary/40 px-4 py-3 text-sm font-medium">
            <BarChart3 className="size-4" aria-hidden />
            Results
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-secondary/30 text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 text-left font-medium">Model</th>
                  <th className="px-4 py-2.5 text-right font-medium">Accuracy</th>
                  <th className="hidden px-4 py-2.5 text-right font-medium md:table-cell">Samples</th>
                  <th className="hidden px-4 py-2.5 text-right font-medium md:table-cell">Time</th>
                </tr>
              </thead>
              <tbody>
                {task.rows.length ? task.rows.map((row) => (
                  <tr key={row.modelName} className="border-b border-border last:border-0 hover:bg-secondary/30">
                    <td className="px-4 py-2.5 font-mono text-xs">{row.modelName}</td>
                    <td className="px-4 py-2.5 text-right font-semibold tabular-nums">{row.accuracy}</td>
                    <td className="hidden px-4 py-2.5 text-right tabular-nums text-muted-foreground md:table-cell">{row.samples}</td>
                    <td className="hidden px-4 py-2.5 text-right tabular-nums text-muted-foreground md:table-cell">{row.executionTime}</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={4} className="px-4 py-10 text-center text-sm text-muted-foreground">
                      No result rows yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        <Card className="space-y-4 p-5">
          <div>
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Submitted models
            </p>
            <div className="mt-2 space-y-2">
              {task.models.length ? task.models.map((model) => (
                <div
                  key={`${model.name}-${model.api_base}`}
                  className="flex items-start gap-2 rounded-md border border-border bg-secondary/30 px-3 py-2"
                >
                  <Bot className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{model.name}</p>
                    <p className="truncate font-mono text-[11px] text-muted-foreground">
                      {model.model_type} · {model.api_base}
                    </p>
                  </div>
                </div>
              )) : (
                <p className="text-sm text-muted-foreground">No model metadata</p>
              )}
            </div>
          </div>
          <Separator />
          <dl className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Created</dt>
              <dd className="font-mono">{task.createdAt}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Completed</dt>
              <dd className="font-mono">{task.completedAt || "—"}</dd>
            </div>
          </dl>
        </Card>
      </div>
    </div>
  );
}

function LeaderboardView(props: {
  loading: string | null;
  query: string;
  setQuery: (query: string) => void;
  suggestion: Suggestion | null;
  suggest: () => Promise<void>;
  categories: { languages: string[]; subjects: string[]; tasks: string[] };
  filters: { language: string; subject: string; taskType: string; limit: number };
  setFilters: React.Dispatch<React.SetStateAction<{ language: string; subject: string; taskType: string; limit: number }>>;
  load: () => void;
  rows: LeaderboardEntry[];
}) {
  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Leaderboard
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Model ranking console</h1>
        </div>
        <Button variant="outline" size="sm" onClick={props.load} disabled={props.loading === "leaderboard"}>
          {props.loading === "leaderboard" ? <Loader2 className="animate-spin" /> : <RefreshCw />}
          Refresh
        </Button>
      </header>

      <Card>
        <div className="flex flex-wrap items-center gap-2 p-3">
          <Sparkles className="size-4 shrink-0 text-accent" aria-hidden />
          <input
            value={props.query}
            onChange={(event) => props.setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void props.suggest();
            }}
            placeholder="Korean math reasoning…"
            className="flex-1 min-w-[180px] bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <Button onClick={() => void props.suggest()} disabled={props.loading === "leaderboard-suggest"}>
            {props.loading === "leaderboard-suggest" ? <Loader2 className="animate-spin" /> : <Search />}
            Search
          </Button>
        </div>
        {props.suggestion ? (
          <div className="border-t border-border bg-secondary/30 px-4 py-2.5 text-xs">
            <span className="font-medium text-foreground">
              {props.suggestion.used_planner ? "AI Planner" : "Fallback"}
            </span>
            <span className="ml-2 text-muted-foreground">{props.suggestion.plan_summary}</span>
          </div>
        ) : null}
      </Card>

      <div className="flex flex-wrap items-end gap-3">
        <Select label="Language" value={props.filters.language} options={props.categories.languages} onChange={(language) => props.setFilters((c) => ({ ...c, language }))} />
        <Select label="Subject" value={props.filters.subject} options={props.categories.subjects} onChange={(subject) => props.setFilters((c) => ({ ...c, subject }))} />
        <Select label="Task" value={props.filters.taskType} options={props.categories.tasks} onChange={(taskType) => props.setFilters((c) => ({ ...c, taskType }))} />
        <FieldNumber
          label="Limit"
          value={props.filters.limit}
          onChange={(limit) => props.setFilters((c) => ({ ...c, limit }))}
        />
        <Button variant="secondary" onClick={props.load}>Apply</Button>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-secondary/50 text-[11px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Rank</th>
                <th className="px-4 py-3 text-left font-medium">Model</th>
                <th className="hidden px-4 py-3 text-left font-medium md:table-cell">Language</th>
                <th className="hidden px-4 py-3 text-left font-medium md:table-cell">Subject</th>
                <th className="hidden px-4 py-3 text-left font-medium md:table-cell">Task</th>
                <th className="px-4 py-3 text-right font-medium">Score</th>
                <th className="hidden px-4 py-3 text-left font-medium md:table-cell">Updated</th>
              </tr>
            </thead>
            <tbody>
              {props.rows.length ? props.rows.map((entry, index) => (
                <tr key={`${entry.id || index}-${entry.model_name}`} className="border-b border-border last:border-0 transition-colors hover:bg-secondary/30">
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">#{index + 1}</td>
                  <td className="px-4 py-3 font-medium">{entry.model_name}</td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    <Badge variant="outline">{entry.language}</Badge>
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground md:table-cell">{entry.subject_type}</td>
                  <td className="hidden px-4 py-3 text-muted-foreground md:table-cell">{entry.task_type}</td>
                  <td className="px-4 py-3 text-right font-semibold tabular-nums">{scoreLabel(entry.score)}</td>
                  <td className="hidden px-4 py-3 text-xs text-muted-foreground md:table-cell">{formatDate(entry.last_updated)}</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-sm text-muted-foreground">
                    No leaderboard rows yet — start an evaluation to populate this list.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  );
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
  );
}

function FieldNumber({ label, value, onChange }: { label: string; value: number; onChange: (n: number) => void }) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
      <input
        type="number"
        min={1}
        value={value}
        onChange={(event) => onChange(Number(event.target.value) || 100)}
        className="h-9 w-24 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      />
    </label>
  );
}

function ManagerView(props: {
  loading: string | null;
  snapshot: ManagerSnapshot | null;
  refresh: () => Promise<void>;
  patchTask: (taskId: string, action: "cancel" | "hold" | "resume" | "restart") => Promise<void>;
  entry: { model: string; language: string; subject: string; taskType: string; score: string };
  setEntry: React.Dispatch<React.SetStateAction<{ model: string; language: string; subject: string; taskType: string; score: string }>>;
  addEntry: () => Promise<void>;
  removeEntry: (entryId?: number) => Promise<void>;
  approveEntry: (entryId?: number) => Promise<void>;
}) {
  const health = props.snapshot?.health || {};
  const capacity = props.snapshot?.capacity || {};
  const healthKeys = ["database", "redis", "celery", "planner", "hret"];

  const healthTone = (status?: string) => {
    if (!status) return "outline" as const;
    if (status === "connected" || status === "available" || status === "healthy") return "success" as const;
    if (status === "no_workers" || status === "unknown") return "secondary" as const;
    return "destructive" as const;
  };

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Manager</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Operations control</h1>
        </div>
        <Button onClick={() => void props.refresh()} disabled={props.loading === "manager"}>
          {props.loading === "manager" ? <Loader2 className="animate-spin" /> : <RefreshCw />}
          Snapshot
        </Button>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {healthKeys.map((key) => (
          <Card key={key} className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{key}</p>
                <p className="mt-1 text-sm font-semibold">{health[key]?.status || "unknown"}</p>
              </div>
              <ShieldCheck className="size-4 text-muted-foreground" aria-hidden />
            </div>
            <Badge variant={healthTone(health[key]?.status)} className="mt-3">
              {health[key]?.status || "unknown"}
            </Badge>
          </Card>
        ))}
      </div>

      {Object.keys(capacity).length ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Object.entries(capacity).map(([key, value]) => (
            <Card key={key} className="p-4">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{key.replace("_", " ")}</p>
              <p className="mt-1 text-2xl font-semibold tabular-nums">{value as number}</p>
            </Card>
          ))}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
        <Card className="overflow-hidden">
          <div className="flex items-center gap-2 border-b border-border bg-secondary/40 px-4 py-3 text-sm font-medium">
            <Server className="size-4" aria-hidden />
            Recent tasks
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-secondary/30 text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 text-left font-medium">Status</th>
                  <th className="px-4 py-2.5 text-left font-medium">Query</th>
                  <th className="hidden px-4 py-2.5 text-left font-medium md:table-cell">Submitted</th>
                  <th className="hidden px-4 py-2.5 text-left font-medium md:table-cell">Models</th>
                  <th className="px-4 py-2.5" />
                </tr>
              </thead>
              <tbody>
                {props.snapshot?.tasks?.length ? props.snapshot.tasks.map((task) => (
                  <tr key={task.task_id} className="border-b border-border last:border-0 hover:bg-secondary/30">
                    <td className="px-4 py-2.5">
                      <Badge variant={
                        normalizeStatus(task.status) === "completed" ? "success" :
                        normalizeStatus(task.status) === "failed" ? "destructive" :
                        normalizeStatus(task.status) === "running" ? "accent" : "secondary"
                      }>
                        {task.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-2.5">{task.query || <span className="text-muted-foreground">—</span>}</td>
                    <td className="hidden px-4 py-2.5 text-xs text-muted-foreground md:table-cell">{formatDate(task.submitted_at)}</td>
                    <td className="hidden px-4 py-2.5 tabular-nums md:table-cell">{task.model_count || "-"}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" title="Restart" onClick={() => void props.patchTask(task.task_id, "restart")}>
                          <RotateCcw className="size-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" title="Hold" onClick={() => void props.patchTask(task.task_id, "hold")}>
                          <Pause className="size-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" title="Cancel" onClick={() => void props.patchTask(task.task_id, "cancel")}>
                          <X className="size-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center text-sm text-muted-foreground">
                      No snapshot loaded — click <span className="font-medium">Snapshot</span> to fetch.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        <Card className="p-5">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Manual entry</p>
          <h3 className="mt-1 text-sm font-semibold">Add leaderboard row</h3>
          <div className="mt-4 space-y-2">
            <input className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm" placeholder="Model" value={props.entry.model} onChange={(event) => props.setEntry((c) => ({ ...c, model: event.target.value }))} />
            <input className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm" placeholder="Language" value={props.entry.language} onChange={(event) => props.setEntry((c) => ({ ...c, language: event.target.value }))} />
            <input className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm" placeholder="Subject" value={props.entry.subject} onChange={(event) => props.setEntry((c) => ({ ...c, subject: event.target.value }))} />
            <input className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm" placeholder="Task type" value={props.entry.taskType} onChange={(event) => props.setEntry((c) => ({ ...c, taskType: event.target.value }))} />
            <input type="number" className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm" placeholder="Score" value={props.entry.score} onChange={(event) => props.setEntry((c) => ({ ...c, score: event.target.value }))} />
            <Button className="w-full" onClick={() => void props.addEntry()}>
              <Plus />
              Save
            </Button>
          </div>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="flex items-center gap-2 border-b border-border bg-secondary/40 px-4 py-3 text-sm font-medium">
          <Trophy className="size-4" aria-hidden />
          Governed leaderboard
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/30 text-[11px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 text-left font-medium">Model</th>
                <th className="hidden px-4 py-2.5 text-left font-medium md:table-cell">Language</th>
                <th className="hidden px-4 py-2.5 text-left font-medium md:table-cell">Subject</th>
                <th className="hidden px-4 py-2.5 text-left font-medium md:table-cell">Task</th>
                <th className="px-4 py-2.5 text-right font-medium">Score</th>
                <th className="hidden px-4 py-2.5 text-left font-medium md:table-cell">Visibility</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {props.snapshot?.leaderboard?.length ? props.snapshot.leaderboard.map((entry) => (
                <tr key={entry.id || entry.model_name} className="border-b border-border last:border-0 hover:bg-secondary/30">
                  <td className="px-4 py-2.5 font-medium">{entry.model_name}</td>
                  <td className="hidden px-4 py-2.5 md:table-cell"><Badge variant="outline">{entry.language}</Badge></td>
                  <td className="hidden px-4 py-2.5 text-muted-foreground md:table-cell">{entry.subject_type}</td>
                  <td className="hidden px-4 py-2.5 text-muted-foreground md:table-cell">{entry.task_type}</td>
                  <td className="px-4 py-2.5 text-right font-semibold tabular-nums">{scoreLabel(entry.score)}</td>
                  <td className="hidden px-4 py-2.5 md:table-cell">
                    <Badge variant={entry.quarantined ? "secondary" : "success"}>
                      {entry.quarantined ? "Pending approval" : "Public"}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {entry.quarantined ? (
                        <Button variant="ghost" size="icon" title="Approve entry" onClick={() => void props.approveEntry(entry.id)}>
                          <CheckCircle2 className="size-3.5" />
                        </Button>
                      ) : null}
                      <Button variant="ghost" size="icon" title="Remove entry" onClick={() => void props.removeEntry(entry.id)}>
                        <Trash2 className="size-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-sm text-muted-foreground">No leaderboard snapshot</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  );
}
