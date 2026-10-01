import { getApiBase, getStoredToken, formatErrorDetail, fetchWithAuth } from "./auth";

export interface ResearchProject {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  research_type: string;
  created_at: string;
  updated_at: string;
}

export interface ResearchRun {
  id: string;
  project_id: string;
  user_id: string;
  question: string;
  status: "queued" | "running" | "completed" | "completed_partial" | "failed" | "cancelled";
  research_iterations: number;
  tool_calls_used: number;
  quality_checks_json?: {
    passed: boolean;
    evidence_count: number;
    source_count: number;
    financial_data_available: boolean;
    unverified_claims_count?: number;
    iteration?: number;
    timestamp?: string;
  } | null;
  model_metadata_json?: {
    report?: {
      title?: string;
      summary?: string;
      content_markdown?: string;
      created_at?: string;
      sources_count?: number;
      evidence_count?: number;
    };
    duration_seconds?: number;
    iteration_count?: number;
    tool_calls_count?: number;
    run_timeout_seconds?: number;
    is_partial?: boolean;
    partial_reason?: string;
    jev_confidence?: number;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchTask {
  id: string;
  research_run_id: string;
  task_type: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  assigned_agent: string;
  input_json?: Record<string, any>;
  output_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Source {
  id: string;
  research_run_id: string;
  url: string;
  title?: string | null;
  publisher?: string | null;
  published_date?: string | null;
  citation_index?: number | null;
  trust_tier: number;
  content_snapshot?: string | null;
  created_at: string;
}

export interface Evidence {
  id: string;
  research_run_id: string;
  source_id?: string | null;
  content: string;
  relevance_score?: number | null;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface Claim {
  id: string;
  research_run_id: string;
  statement: string;
  claim_type: "fact" | "analysis" | "scenario" | "uncertainty";
  status: "supported" | "unverified" | "disputed";
  confidence?: number | null;
  created_at: string;
}

export interface JevEvaluation {
  id: string;
  research_run_id: string;
  question_id: string;
  choice_value: string;
  confidence: number;
  probabilities_json: Record<string, number>;
  model_version: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// API Methods
// ---------------------------------------------------------------------------

export async function listProjects(): Promise<ResearchProject[]> {
  const res = await fetchWithAuth("/api/v1/research/projects");
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(errorData));
  }
  return res.json();
}

export async function createProject(name: string, researchType: string = "equity"): Promise<ResearchProject> {
  const res = await fetchWithAuth("/api/v1/research/projects", {
    method: "POST",
    body: JSON.stringify({ name, research_type: researchType }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(errorData));
  }
  return res.json();
}

export async function listRuns(projectId: string): Promise<ResearchRun[]> {
  const res = await fetchWithAuth(`/api/v1/research/projects/${projectId}/runs`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(errorData));
  }
  return res.json();
}

export async function getRun(runId: string): Promise<ResearchRun> {
  const res = await fetchWithAuth(`/api/v1/research/runs/${runId}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(errorData));
  }
  return res.json();
}

export async function createAndStartRun(projectId: string, question: string): Promise<ResearchRun> {
  const idempotencyKey = `web_run_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  const res = await fetchWithAuth(`/api/v1/research/projects/${projectId}/runs?execute_now=true`, {
    method: "POST",
    headers: {
      "X-Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({ question, idempotency_key: idempotencyKey }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(errorData));
  }
  return res.json();
}

export async function getRunTasks(runId: string): Promise<ResearchTask[]> {
  const res = await fetchWithAuth(`/api/v1/research/runs/${runId}/tasks`);
  if (!res.ok) return [];
  return res.json();
}

export async function getRunEvidence(runId: string): Promise<Evidence[]> {
  const res = await fetchWithAuth(`/api/v1/research/runs/${runId}/evidence`);
  if (!res.ok) return [];
  return res.json();
}

export async function getRunSources(runId: string): Promise<Source[]> {
  const res = await fetchWithAuth(`/api/v1/research/runs/${runId}/sources`);
  if (!res.ok) return [];
  return res.json();
}

export async function getRunClaims(runId: string): Promise<Claim[]> {
  const res = await fetchWithAuth(`/api/v1/research/runs/${runId}/claims`);
  if (!res.ok) return [];
  return res.json();
}

export async function getRunJevEvaluations(runId: string): Promise<JevEvaluation[]> {
  const res = await fetchWithAuth(`/api/v1/research/runs/${runId}/jev-evaluations`);
  if (!res.ok) return [];
  return res.json();
}

// ---------------------------------------------------------------------------
// SSE Stream Consumer with Replay-Then-Subscribe (§23)
// ---------------------------------------------------------------------------

export interface SSECallbacks {
  onSnapshot?: (snapshotData: any) => void;
  onEvent?: (eventType: string, eventData: any) => void;
  onComplete?: (status: string) => void;
  onError?: (err: Error) => void;
}

export function subscribeToResearchRunSSE(
  runId: string,
  callbacks: SSECallbacks
): () => void {
  let isCancelled = false;
  const abortController = new AbortController();

  async function startStreaming() {
    try {
      const token = getStoredToken();
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/api/v1/research/runs/${runId}/stream`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "text/event-stream",
        },
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`SSE stream connection failed with HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error("No readable body in SSE response");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (!isCancelled) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.trim()) continue;
          const lines = part.split("\n");
          let eventName = "message";
          let dataStr = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventName = line.substring(7).trim();
            } else if (line.startsWith("data: ")) {
              dataStr = line.substring(6).trim();
            }
          }

          if (dataStr) {
            try {
              const parsed = JSON.parse(dataStr);
              if (eventName === "snapshot" && callbacks.onSnapshot) {
                callbacks.onSnapshot(parsed);
              } else if (eventName === "end" && callbacks.onComplete) {
                callbacks.onComplete(parsed.status || "completed");
              } else if (callbacks.onEvent) {
                callbacks.onEvent(eventName, parsed);
              }
            } catch (err) {
              console.warn("Could not parse SSE JSON payload:", dataStr, err);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError" && !isCancelled) {
        console.error("SSE stream error:", err);
        callbacks.onError?.(err);
      }
    }
  }

  startStreaming();

  return () => {
    isCancelled = true;
    abortController.abort();
  };
}
