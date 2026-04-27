"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Loader2,
  Lock,
  MessageSquare,
  Plus,
  Send,
  Settings2,
  Sparkles,
  SquarePen,
  Trash2,
  Trophy
} from "lucide-react";

import { ApiError, api } from "@/services/api";
import type {
  ChatLookup,
  ChatMessage,
  EvaluationDraft,
  EvaluationSpec,
  ModelConfig
} from "@/services/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const SAMPLE_OPTIONS = [
  { id: "small", label: "Small (50)" },
  { id: "medium", label: "Medium (100)" },
  { id: "large", label: "Large (250)" },
  { id: "full", label: "Full (500)" }
];

const SLOT_LABELS: Record<string, string> = {
  query: "Goal",
  category_language: "Language",
  category_subject: "Subject",
  category_task_type: "Task type",
  sample_scale: "Sample size"
};

const REQUIRED_SLOTS = Object.keys(SLOT_LABELS);

const blankModel = (index: number): ModelConfig => ({
  name: `model_${index}`,
  api_base: "https://api.openai.com/v1",
  api_key: "",
  model_type: "openai"
});

type LaunchState = "idle" | "launching" | "launched";

type Props = {
  onLaunched: (taskId: string) => void;
  onError: (message: string) => void;
  /**
   * If provided, mount with this specific draft (e.g. when the user picks a
   * draft from the sidebar history). When `null`/omitted, the view falls back
   * to the most recent ongoing draft or creates a new one.
   */
  activeDraftId?: number | null;
  /**
   * Fires whenever the local draft state changes (initial load, send,
   * fresh-start, launch). Lets the parent keep the sidebar in sync without
   * round-tripping through the drafts list endpoint on every keystroke.
   */
  onDraftChanged?: (draft: EvaluationDraft | null) => void;
  /**
   * Asks the parent to fork the given draft id into a new editable copy and
   * route the user there. Used when the user opens a launched (locked) thread
   * and wants to make changes.
   */
  onFork?: (sourceDraftId: number) => void | Promise<void>;
};

export default function EvaluationChatView({
  onLaunched,
  onError,
  activeDraftId,
  onDraftChanged,
  onFork
}: Props) {
  const [draft, setDraft] = useState<EvaluationDraft | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [composer, setComposer] = useState("");
  const [sending, setSending] = useState(false);
  const [models, setModels] = useState<ModelConfig[]>([blankModel(1)]);
  const [launchState, setLaunchState] = useState<LaunchState>("idle");
  const [activePane, setActivePane] = useState<"chat" | "spec">("chat");
  const [forking, setForking] = useState(false);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);
  const scrollAnchor = useRef<HTMLDivElement | null>(null);

  // Parent callbacks captured in refs. Inline arrow props from the parent are
  // recreated every render, which would otherwise force every callback that
  // depends on them to also re-create — that bug was busy-looping ensureDraft
  // and freezing the panel.
  const onErrorRef = useRef(onError);
  const onDraftChangedRef = useRef(onDraftChanged);
  const onLaunchedRef = useRef(onLaunched);
  const onForkRef = useRef(onFork);
  useEffect(() => {
    onErrorRef.current = onError;
    onDraftChangedRef.current = onDraftChanged;
    onLaunchedRef.current = onLaunched;
    onForkRef.current = onFork;
  }, [onError, onDraftChanged, onLaunched, onFork]);

  // Notify the parent on every draft mutation so History can stack the entry
  // as soon as the conversation starts (rather than waiting for launch).
  useEffect(() => {
    onDraftChangedRef.current?.(draft);
  }, [draft]);

  const spec = draft?.spec ?? {};
  const messages: ChatMessage[] = useMemo(() => draft?.messages ?? [], [draft]);
  const missingSlots = draft?.missing_slots ?? REQUIRED_SLOTS;
  const specComplete = missingSlots.length === 0;
  const hasUsableModel = models.some(
    (m) => m.name.trim() && m.api_key.trim() && m.api_base.trim()
  );
  const canLaunch =
    !!draft &&
    draft.status === "draft" &&
    specComplete &&
    hasUsableModel &&
    launchState !== "launching";

  const draftId = draft?.id ?? null;

  const ensureDraft = useCallback(async () => {
    // The sidebar tells us "go to draft X" by setting activeDraftId. If we
    // already have that draft loaded (e.g. because we're the ones who told
    // the parent about it after a fresh create), skip the round-trip.
    if (activeDraftId != null && draftId === activeDraftId) return;
    setBootError(null);
    try {
      if (activeDraftId != null) {
        const target = await api.getDraft(activeDraftId);
        setDraft(target);
        setLaunchState(target.status === "launched" ? "launched" : "idle");
        return;
      }
      const list = await api.listDrafts(20);
      const ongoing = (list.drafts || []).find((d) => d.status === "draft");
      if (ongoing) {
        setDraft(ongoing);
        return;
      }
      const created = await api.createDraft();
      setDraft(created);
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Failed to load drafts";
      setBootError(msg);
      onErrorRef.current?.(msg);
    }
  }, [activeDraftId, draftId]);

  useEffect(() => {
    void ensureDraft();
  }, [ensureDraft]);

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  useEffect(() => {
    const suggested = spec.suggested_models;
    if (!suggested || suggested.length === 0) return;
    setModels((current) => {
      const filled = current.filter((m) => m.name.trim() && m.api_key.trim());
      if (filled.length > 0) return current;
      return suggested.slice(0, 5).map((s, i) => ({
        name: s.name,
        api_base: s.api_base || blankModel(i + 1).api_base,
        api_key: "",
        model_type: (s.model_type as ModelConfig["model_type"]) || "openai"
      }));
    });
  }, [spec.suggested_models]);

  const send = useCallback(async () => {
    if (!draft || !composer.trim() || sending) return;
    const text = composer.trim();
    setComposer("");
    setSending(true);

    const optimistic: EvaluationDraft = {
      ...draft,
      messages: [...draft.messages, { role: "user", content: text }]
    };
    setDraft(optimistic);

    try {
      const next = await api.sendDraftMessage(draft.id, text);
      setDraft(next);
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Send failed";
      onErrorRef.current?.(msg);
      setDraft(draft);
    } finally {
      setSending(false);
      composerRef.current?.focus();
    }
  }, [composer, draft, sending]);

  const launch = useCallback(async () => {
    if (!draft || !canLaunch) return;
    setLaunchState("launching");
    try {
      const usable = models.filter(
        (m) => m.name.trim() && m.api_key.trim() && m.api_base.trim()
      );
      const result = await api.launchDraft(draft.id, usable);
      setLaunchState("launched");
      onLaunchedRef.current?.(result.task_id);
    } catch (error) {
      setLaunchState("idle");
      const msg =
        error instanceof ApiError ? error.detail : (error as Error).message;
      onErrorRef.current?.(msg || "Launch failed");
    }
  }, [canLaunch, draft, models]);

  const startFreshDraft = useCallback(async () => {
    setLaunchState("idle");
    setComposer("");
    setModels([blankModel(1)]);
    try {
      const created = await api.createDraft();
      setDraft(created);
    } catch (error) {
      onErrorRef.current?.(
        error instanceof Error ? error.message : "Could not create a new draft"
      );
    }
  }, []);

  const isLocked = !!draft && draft.status !== "draft";

  const fork = useCallback(async () => {
    if (!draft || !onForkRef.current || forking) return;
    setForking(true);
    try {
      await onForkRef.current(draft.id);
    } finally {
      setForking(false);
    }
  }, [draft, forking]);

  if (!draft && !bootError) {
    return (
      <section
        className="grid min-h-[60vh] place-items-center"
        aria-busy="true"
      >
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </section>
    );
  }

  if (!draft) {
    return (
      <section className="flex flex-col items-center gap-3 py-12">
        <p className="text-sm text-destructive" role="alert">{bootError}</p>
        <Button onClick={() => void ensureDraft()}>Retry</Button>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-4">
      {isLocked ? (
        <div
          role="status"
          aria-live="polite"
          className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-secondary/60 px-4 py-3 text-sm"
        >
          <Lock className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="font-medium">
              {draft.status === "launched" ? "Thread launched" : "Thread archived"}
            </p>
            <p className="text-xs text-muted-foreground">
              {draft.status === "launched" && draft.launched_task_id
                ? `Linked to task ${draft.launched_task_id.slice(0, 8)}. Fork to make changes and run as a new evaluation.`
                : "This conversation is read-only. Fork it to keep iterating."}
            </p>
          </div>
          {onFork ? (
            <Button
              size="sm"
              variant="default"
              type="button"
              onClick={() => void fork()}
              disabled={forking}
            >
              {forking ? <Loader2 className="animate-spin" /> : <SquarePen />}
              Edit & fork
            </Button>
          ) : null}
        </div>
      ) : null}

      {/* Mobile pane switcher */}
      <div className="flex items-center justify-center md:hidden">
        <div className="inline-flex rounded-lg border border-border bg-card p-1 text-sm">
          <button
            type="button"
            onClick={() => setActivePane("chat")}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors",
              activePane === "chat"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <MessageSquare className="size-3.5" /> Chat
          </button>
          <button
            type="button"
            onClick={() => setActivePane("spec")}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors",
              activePane === "spec"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Settings2 className="size-3.5" /> Spec
            {specComplete ? <Check className="size-3.5" /> : null}
          </button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-[minmax(0,1.4fr)_minmax(360px,1fr)]">
        <ChatPane
          show={activePane === "chat"}
          messages={messages}
          composer={composer}
          setComposer={setComposer}
          send={send}
          sending={sending}
          locked={isLocked}
          composerRef={composerRef}
          scrollAnchor={scrollAnchor}
        />

        <SpecPane
          show={activePane === "spec"}
          spec={spec}
          missingSlots={missingSlots}
          models={models}
          setModels={setModels}
          launch={launch}
          canLaunch={canLaunch}
          launchState={launchState}
          launchedTaskId={draft.launched_task_id || null}
          status={draft.status}
          onStartFresh={startFreshDraft}
        />
      </div>
    </section>
  );
}

// --- chat pane --------------------------------------------------------------

function ChatPane({
  show,
  messages,
  composer,
  setComposer,
  send,
  sending,
  locked,
  composerRef,
  scrollAnchor
}: {
  show: boolean;
  messages: ChatMessage[];
  composer: string;
  setComposer: (next: string) => void;
  send: () => void;
  sending: boolean;
  locked: boolean;
  composerRef: React.MutableRefObject<HTMLTextAreaElement | null>;
  scrollAnchor: React.MutableRefObject<HTMLDivElement | null>;
}) {
  return (
    <Card
      className={cn(
        "flex h-[calc(100vh-180px)] min-h-[480px] flex-col overflow-hidden",
        !show && "hidden md:flex"
      )}
    >
      <div
        className="flex-1 space-y-4 overflow-y-auto p-6"
        role="log"
        aria-live="polite"
      >
        {messages.length === 0 ? <ChatPrompt /> : null}
        {messages.map((message, index) => (
          <ChatBubble key={index} message={message} />
        ))}
        {sending ? (
          <div className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-muted-foreground">
            <Sparkles className="size-3.5" aria-hidden />
            <TypingDots />
          </div>
        ) : null}
        <div ref={scrollAnchor} />
      </div>

      <Separator />

      <form
        className="flex items-end gap-2 p-4"
        onSubmit={(event) => {
          event.preventDefault();
          send();
        }}
      >
        <Label htmlFor="eval-composer" className="sr-only">
          Message
        </Label>
        <Textarea
          id="eval-composer"
          ref={composerRef}
          rows={2}
          placeholder={
            locked
              ? "This thread is locked. Fork it to keep editing."
              : "Tell me what you want to evaluate, or ask if it already exists…"
          }
          value={composer}
          onChange={(event) => setComposer(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              send();
            }
          }}
          disabled={locked}
          className="min-h-[44px] resize-none"
        />
        <Button
          type="submit"
          size="icon"
          disabled={sending || locked || !composer.trim()}
          aria-label="Send message"
        >
          {sending ? <Loader2 className="animate-spin" /> : <Send />}
        </Button>
      </form>
    </Card>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex gap-1" aria-label="Assistant is typing">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="size-1.5 animate-bounce rounded-full bg-muted-foreground"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}

function ChatPrompt() {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/40 p-5">
      <div className="mb-2 inline-flex items-center gap-2 text-sm font-medium">
        <Sparkles className="size-4 text-accent" aria-hidden />
        Describe an evaluation
      </div>
      <p className="text-sm text-muted-foreground">
        I'll first check whether existing leaderboard runs already answer it
        before suggesting a fresh run.
      </p>
      <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
        <li>• "Korean math reasoning across small models"</li>
        <li>• "Compare GPT-4o and Claude on English coding"</li>
        <li>• "What scores do we already have for science knowledge?"</li>
      </ul>
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div
      className={cn(
        "flex flex-col gap-1.5 animate-fade-in",
        isUser ? "items-end" : "items-start"
      )}
    >
      <div
        className={cn(
          "max-w-[88%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "rounded-br-md bg-primary text-primary-foreground"
            : "rounded-bl-md border border-border bg-card text-card-foreground"
        )}
      >
        <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-wider opacity-70">
          <span>{isUser ? "You" : "Planner"}</span>
          {message.created_at ? (
            <time>{message.created_at.replace("T", " ").slice(11, 16)}</time>
          ) : null}
        </div>
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
      {message.lookups?.length ? (
        <div className="w-full max-w-[88%] space-y-2">
          {message.lookups.map((lookup, index) => (
            <LookupCard key={index} lookup={lookup} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function LookupCard({ lookup }: { lookup: ChatLookup }) {
  if (!lookup.entries.length) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-dashed border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
        <Trophy className="size-3.5" aria-hidden />
        No matching leaderboard rows yet — a fresh run would fill this in.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border bg-muted/40 px-3 py-2 text-xs font-medium">
        <Trophy className="size-3.5 text-accent" aria-hidden />
        Existing leaderboard
        <Badge variant="secondary" className="ml-auto">
          {lookup.entries.length}
        </Badge>
      </div>
      <table className="w-full text-xs">
        <thead className="text-muted-foreground">
          <tr className="border-b border-border">
            <th className="px-3 py-2 text-left font-medium">Model</th>
            <th className="px-3 py-2 text-right font-medium">Score</th>
            <th className="hidden px-3 py-2 text-left font-medium md:table-cell">Subject</th>
            <th className="hidden px-3 py-2 text-left font-medium md:table-cell">Task</th>
          </tr>
        </thead>
        <tbody>
          {lookup.entries.slice(0, 8).map((entry) => (
            <tr key={entry.id || entry.model_name} className="border-b border-border last:border-0">
              <td className="px-3 py-2 font-mono text-[11px]">{entry.model_name}</td>
              <td className="px-3 py-2 text-right tabular-nums">
                {entry.score?.toFixed?.(2) ?? "-"}
              </td>
              <td className="hidden px-3 py-2 text-muted-foreground md:table-cell">
                {entry.subject_type}
              </td>
              <td className="hidden px-3 py-2 text-muted-foreground md:table-cell">
                {entry.task_type}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- spec pane --------------------------------------------------------------

function SpecPane({
  show,
  spec,
  missingSlots,
  models,
  setModels,
  launch,
  canLaunch,
  launchState,
  launchedTaskId,
  status,
  onStartFresh
}: {
  show: boolean;
  spec: EvaluationSpec;
  missingSlots: string[];
  models: ModelConfig[];
  setModels: React.Dispatch<React.SetStateAction<ModelConfig[]>>;
  launch: () => void;
  canLaunch: boolean;
  launchState: LaunchState;
  launchedTaskId: string | null;
  status: EvaluationDraft["status"];
  onStartFresh: () => void;
}) {
  const updateModel = (index: number, patch: Partial<ModelConfig>) => {
    setModels((current) => current.map((m, i) => (i === index ? { ...m, ...patch } : m)));
  };
  const addModel = () =>
    setModels((current) =>
      current.length >= 5 ? current : [...current, blankModel(current.length + 1)]
    );
  const removeModel = (index: number) =>
    setModels((current) => (current.length === 1 ? current : current.filter((_, i) => i !== index)));

  const filledCount = REQUIRED_SLOTS.length - missingSlots.length;

  return (
    <Card className={cn("flex max-h-[calc(100vh-180px)] flex-col overflow-y-auto", !show && "hidden md:flex")}>
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Live spec
            </p>
            <CardTitle className="text-base">
              {spec.query?.slice(0, 90) || "Untitled evaluation"}
            </CardTitle>
          </div>
          {status === "launched" ? (
            <Button variant="outline" size="sm" onClick={onStartFresh} type="button">
              New draft
            </Button>
          ) : null}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{filledCount}/{REQUIRED_SLOTS.length} slots filled</span>
          <div className="flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-1 rounded-full bg-foreground transition-all"
              style={{ width: `${(filledCount / REQUIRED_SLOTS.length) * 100}%` }}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <ul className="space-y-1.5">
          {REQUIRED_SLOTS.map((slot) => {
            const filled = !missingSlots.includes(slot);
            const value = (spec as Record<string, unknown>)[slot] as string | undefined;
            return (
              <li
                key={slot}
                className={cn(
                  "flex items-center gap-3 rounded-md border px-3 py-2 text-sm transition-colors",
                  filled
                    ? "border-foreground/15 bg-secondary/60"
                    : "border-dashed border-border bg-transparent text-muted-foreground"
                )}
              >
                <CheckCircle2
                  className={cn(
                    "size-4 shrink-0",
                    filled ? "text-foreground" : "text-muted-foreground/50"
                  )}
                  aria-hidden
                />
                <span className="font-medium">{SLOT_LABELS[slot]}</span>
                <span className="ml-auto truncate text-right text-muted-foreground">
                  {value || "—"}
                </span>
              </li>
            );
          })}
        </ul>

        <Separator />

        <section className="space-y-3">
          <header className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Models</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={addModel}
              disabled={models.length >= 5}
              type="button"
            >
              <Plus className="size-3.5" /> Add
            </Button>
          </header>
          <p className="text-xs text-muted-foreground">
            API keys stay in this browser session — they're posted directly to the run endpoint, not stored with the draft.
          </p>
          <div className="space-y-3">
            {models.map((model, index) => (
              <div
                key={index}
                className="space-y-2 rounded-lg border border-border bg-secondary/30 p-3"
              >
                <div className="flex gap-2">
                  <Input
                    aria-label="Model name"
                    placeholder="model_name"
                    value={model.name}
                    onChange={(event) => updateModel(index, { name: event.target.value })}
                    className="font-mono text-xs"
                  />
                  <select
                    aria-label="Model type"
                    value={model.model_type}
                    onChange={(event) =>
                      updateModel(index, {
                        model_type: event.target.value as ModelConfig["model_type"]
                      })
                    }
                    className="h-9 rounded-md border border-input bg-background px-2 text-xs shadow-sm"
                  >
                    <option value="openai">openai</option>
                    <option value="anthropic">anthropic</option>
                    <option value="huggingface">huggingface</option>
                    <option value="custom">custom</option>
                  </select>
                  {models.length > 1 ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={`Remove ${model.name || "model"}`}
                      onClick={() => removeModel(index)}
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                  ) : null}
                </div>
                <Input
                  aria-label="API base URL"
                  placeholder="https://api.openai.com/v1"
                  value={model.api_base}
                  onChange={(event) => updateModel(index, { api_base: event.target.value })}
                  className="font-mono text-xs"
                />
                <Input
                  aria-label="API key"
                  type="password"
                  autoComplete="off"
                  placeholder="sk-…"
                  value={model.api_key}
                  onChange={(event) => updateModel(index, { api_key: event.target.value })}
                  className="font-mono text-xs"
                />
              </div>
            ))}
          </div>
        </section>

        {spec.sample_scale ? (
          <p className="text-xs text-muted-foreground">
            Sample size: <span className="font-medium text-foreground">{labelForScale(spec.sample_scale)}</span>
          </p>
        ) : null}
      </CardContent>

      <div className="mt-auto space-y-2 border-t border-border bg-card p-6">
        <Button
          type="button"
          size="lg"
          className="w-full"
          disabled={!canLaunch}
          onClick={launch}
        >
          {launchState === "launching" ? (
            <>
              <Loader2 className="animate-spin" /> Launching…
            </>
          ) : launchState === "launched" ? (
            <>
              <CheckCircle2 /> Launched
            </>
          ) : (
            <>
              RUN evaluation <ArrowRight />
            </>
          )}
        </Button>
        {!canLaunch && launchState !== "launched" ? (
          <p className="text-xs text-muted-foreground">
            {missingSlots.length
              ? `Still need: ${missingSlots.map((s) => SLOT_LABELS[s]).join(", ")}`
              : "Add at least one model with an API key to RUN."}
          </p>
        ) : null}
        {launchState === "launched" && launchedTaskId ? (
          <p className="text-xs text-muted-foreground">
            Task <code className="font-mono text-foreground">{launchedTaskId.slice(0, 8)}</code> queued. Watch progress in the sidebar.
          </p>
        ) : null}
      </div>
    </Card>
  );
}

function labelForScale(scale: string) {
  const preset = SAMPLE_OPTIONS.find((o) => o.id === scale);
  if (preset) return preset.label;
  if (scale.startsWith("custom:")) return `Custom (${scale.slice(7)})`;
  return scale;
}
