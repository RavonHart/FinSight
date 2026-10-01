"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  Search,
  Plus,
  RefreshCw,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  ChevronRight,
  FolderOpen,
  ArrowLeft,
  Briefcase,
  History,
  X,
  Send,
  Zap,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";
import {
  ResearchProject,
  ResearchRun,
  ResearchTask,
  Source,
  Evidence,
  Claim,
  JevEvaluation,
  listProjects,
  createProject,
  listRuns,
  createAndStartRun,
  getRun,
  getRunTasks,
  getRunEvidence,
  getRunSources,
  getRunClaims,
  getRunJevEvaluations,
  subscribeToResearchRunSSE,
} from "@/lib/research";
import { ResearchPlanPanel } from "@/components/research-plan-panel";
import { MarkdownReport } from "@/components/markdown-report";
import { EvidenceProvenancePanel } from "@/components/evidence-provenance-panel";

const PRESET_RESEARCH_PROMPTS = [
  "Research NVIDIA: evaluate datacenter revenue sustainability, Blackwell GPU roadmap, and antitrust risks",
  "Analyze Apple: evaluate services margin expansion, AI integration, and China sales headwinds",
  "Evaluate Microsoft: Azure cloud growth, OpenAI partnership, and CapEx intensity",
];

export default function ResearchWorkspacePage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();

  // Project & Run State
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [activeProject, setActiveProject] = useState<ResearchProject | null>(null);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [activeRun, setActiveRun] = useState<ResearchRun | null>(null);

  // Run Artifacts & Diagnostics
  const [tasks, setTasks] = useState<ResearchTask[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [jevEvaluations, setJevEvaluations] = useState<JevEvaluation[]>([]);

  // UI State
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isStartingRun, setIsStartingRun] = useState<boolean>(false);
  const [showNewRunModal, setShowNewRunModal] = useState<boolean>(false);
  const [newRunQuestion, setNewRunQuestion] = useState<string>("");
  const [activeCitation, setActiveCitation] = useState<number | null>(null);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const unsubscribeRef = useRef<(() => void) | null>(null);

  // Authentication Guard
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
    }
  }, [user, isAuthLoading, router]);

  // Load Projects on Initial Mount
  useEffect(() => {
    if (!user) return;

    let isMounted = true;
    async function initProjects() {
      try {
        setIsLoading(true);
        let projs = await listProjects();
        if (projs.length === 0) {
          // Auto-seed default research project
          const defaultProj = await createProject("Equity Research Alpha", "equity");
          projs = [defaultProj];
        }
        if (isMounted) {
          setProjects(projs);
          setActiveProject(projs[0]);
        }
      } catch (err: any) {
        if (isMounted) setErrorMessage(err.message || "Failed to load projects");
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    initProjects();
    return () => {
      isMounted = false;
    };
  }, [user]);

  // Load Runs when Active Project changes
  useEffect(() => {
    if (!activeProject) return;

    let isMounted = true;
    async function loadProjectRuns() {
      try {
        const runList = await listRuns(activeProject.id);
        if (isMounted) {
          setRuns(runList);
          if (runList.length > 0 && !activeRun) {
            setActiveRun(runList[0]);
          }
        }
      } catch (err: any) {
        console.error("Error loading project runs:", err);
      }
    }

    loadProjectRuns();
    return () => {
      isMounted = false;
    };
  }, [activeProject]);

  // Refresh active run artifacts (tasks, sources, evidence, claims, jev)
  const refreshRunArtifacts = useCallback(async (runId: string) => {
    try {
      const [tList, sList, eList, cList, jList] = await Promise.all([
        getRunTasks(runId),
        getRunSources(runId),
        getRunEvidence(runId),
        getRunClaims(runId),
        getRunJevEvaluations(runId),
      ]);
      setTasks(tList);
      setSources(sList);
      setEvidence(eList);
      setClaims(cList);
      setJevEvaluations(jList);
    } catch (err) {
      console.warn("Error refreshing run artifacts:", err);
    }
  }, []);

  // Connect to SSE Stream whenever activeRun changes or status is running
  useEffect(() => {
    if (!activeRun) return;

    // Fetch latest DB state for artifacts
    refreshRunArtifacts(activeRun.id);

    // Clean up any existing SSE subscription
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }

    // Subscribe to SSE stream (Replay-Then-Subscribe §23)
    const unsub = subscribeToResearchRunSSE(activeRun.id, {
      onSnapshot: (snapshot) => {
        setActiveRun((prev) => {
          if (!prev || prev.id !== snapshot.run_id) return prev;
          return {
            ...prev,
            status: snapshot.status,
            research_iterations: snapshot.research_iterations,
            tool_calls_used: snapshot.tool_calls_used,
            model_metadata_json: {
              ...prev.model_metadata_json,
              report: snapshot.report || prev.model_metadata_json?.report,
            },
          };
        });
        if (snapshot.tasks && Array.isArray(snapshot.tasks)) {
          setTasks(snapshot.tasks);
        }
      },
      onEvent: (eventName, eventData) => {
        if (eventName === "task_started") {
          setActiveStep(eventData.task_type || eventData.task || null);
          refreshRunArtifacts(activeRun.id);
        } else if (eventName === "task_completed") {
          refreshRunArtifacts(activeRun.id);
        } else if (eventName === "evidence_collected") {
          setActiveStep("evidence_validation");
          refreshRunArtifacts(activeRun.id);
        } else if (eventName === "jev_analysis_completed") {
          setActiveStep("jev_analysis");
          refreshRunArtifacts(activeRun.id);
        } else if (eventName === "run_completed" || eventName === "run_completed_partial") {
          setActiveStep(null);
          setActiveRun((prev) => (prev ? { ...prev, status: eventData.status || "completed" } : prev));
          refreshRunArtifacts(activeRun.id);
        }
      },
      onComplete: (terminalStatus) => {
        setActiveStep(null);
        setActiveRun((prev) =>
          prev ? { ...prev, status: terminalStatus as ResearchRun["status"] } : prev
        );
        refreshRunArtifacts(activeRun.id);
      },
      onError: (err) => {
        console.warn("SSE stream notice:", err);
      },
    });

    unsubscribeRef.current = unsub;

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
    };
  }, [activeRun?.id, refreshRunArtifacts]);

  // Handle Triggering a New Research Run
  const handleStartRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject || !newRunQuestion.trim()) return;

    try {
      setIsStartingRun(true);
      setErrorMessage(null);
      const newRun = await createAndStartRun(activeProject.id, newRunQuestion.trim());

      setRuns((prev) => [newRun, ...prev]);
      setActiveRun(newRun);
      setNewRunQuestion("");
      setShowNewRunModal(false);

      // Refresh project run list
      const updated = await listRuns(activeProject.id);
      setRuns(updated);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to initiate research run");
    } finally {
      setIsStartingRun(false);
    }
  };

  if (isLoading || isAuthLoading) {
    return (
      <div className="min-h-screen bg-[#090d16] flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  const reportMarkdown = activeRun?.model_metadata_json?.report?.content_markdown || "";
  const partialReason = activeRun?.model_metadata_json?.partial_reason;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              href="/app/dashboard"
              className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Dashboard</span>
            </Link>

            <div className="h-4 w-px bg-slate-800" />

            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Search className="h-4 w-4 text-white" />
              </div>
              <span className="text-base font-bold text-white tracking-tight">Research Workspace</span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                §26 Three-Panel
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Run History Drawer Button */}
            <button
              onClick={() => setShowHistoryDrawer(!showHistoryDrawer)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-xs font-medium text-slate-300 transition"
            >
              <History className="h-3.5 w-3.5 text-blue-400" />
              <span>Run History ({runs.length})</span>
            </button>

            {/* Launch New Run Button */}
            <button
              onClick={() => setShowNewRunModal(true)}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-lg shadow-blue-500/20 transition transform active:scale-95"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Research Run</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-6 py-4 flex flex-col space-y-4">
        {/* Active Question Banner & Controls */}
        <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 backdrop-blur-md flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Research Inquiry
              </span>
              {activeRun && (
                <span className="text-[10px] font-mono text-slate-500">
                  ID: {activeRun.id.substring(0, 8)}...
                </span>
              )}
            </div>
            <h1 className="text-base font-bold text-white tracking-tight">
              {activeRun?.question || "No research run selected"}
            </h1>
          </div>

          {activeRun && (
            <div className="flex items-center space-x-3 shrink-0">
              <div className="text-right">
                <div className="text-[11px] font-medium text-slate-400">Status</div>
                <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
                  {activeRun.status === "running" && (
                    <Loader2 className="h-3 w-3 text-blue-400 animate-spin" />
                  )}
                  {activeRun.status === "completed" && (
                    <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                  )}
                  {activeRun.status === "completed_partial" && (
                    <AlertTriangle className="h-3 w-3 text-amber-400" />
                  )}
                  <span>{activeRun.status.replace("_", " ")}</span>
                </div>
              </div>

              <button
                onClick={() => refreshRunArtifacts(activeRun.id)}
                title="Refresh State"
                className="p-2 rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-white transition"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-200 text-xs flex items-center justify-between">
            <span>{errorMessage}</span>
            <button onClick={() => setErrorMessage(null)}>
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* THREE-PANEL RESEARCH WORKSPACE (§26) */}
        {activeRun ? (
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-[680px]">
            {/* Left Panel: Research Plan & Tasks + Jev System One (3 cols) */}
            <div className="lg:col-span-3 h-[680px]">
              <ResearchPlanPanel
                tasks={tasks}
                jevEvaluations={jevEvaluations}
                runStatus={activeRun.status}
                iterations={activeRun.research_iterations}
                toolCalls={activeRun.tool_calls_used}
                activeStep={activeStep}
              />
            </div>

            {/* Center Panel: Synthesized Markdown Report with UX Honesty (6 cols) */}
            <div className="lg:col-span-6 h-[680px]">
              <MarkdownReport
                markdown={reportMarkdown}
                status={activeRun.status}
                partialReason={partialReason}
                sources={sources}
                activeCitation={activeCitation}
                onSelectCitation={(citeNum) => setActiveCitation(citeNum)}
                runIterations={activeRun.research_iterations}
                toolCallsUsed={activeRun.tool_calls_used}
              />
            </div>

            {/* Right Panel: Evidence & Sources Provenance (3 cols) */}
            <div className="lg:col-span-3 h-[680px]">
              <EvidenceProvenancePanel
                sources={sources}
                evidence={evidence}
                claims={claims}
                activeCitation={activeCitation}
                onSelectCitation={(citeNum) => setActiveCitation(citeNum)}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-12 border border-dashed border-slate-800 rounded-2xl bg-slate-900/20 text-center">
            <Search className="h-12 w-12 text-slate-600 mb-4" />
            <h2 className="text-base font-bold text-white">No Research Runs Yet</h2>
            <p className="text-xs text-slate-400 max-w-md mt-1 mb-6">
              Launch your first agentic financial research run to synthesize evidence across financial metrics, competitive positioning, catalysts, and Jev System One judgments.
            </p>
            <button
              onClick={() => setShowNewRunModal(true)}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-lg shadow-blue-500/20 transition"
            >
              <Plus className="h-4 w-4" />
              <span>Start First Research Run</span>
            </button>
          </div>
        )}
      </main>

      {/* History Slide-Over Drawer */}
      {showHistoryDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setShowHistoryDrawer(false)}
          />
          <div className="relative w-full max-w-md bg-[#0a0f1d] border-l border-slate-800/80 shadow-2xl z-10 flex flex-col h-full">
            <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <History className="h-4 w-4 text-blue-400" />
                <h3 className="text-sm font-bold text-white">Run History</h3>
              </div>
              <button
                onClick={() => setShowHistoryDrawer(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
              {runs.map((r) => {
                const isSelected = activeRun?.id === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => {
                      setActiveRun(r);
                      setShowHistoryDrawer(false);
                    }}
                    className={`p-3.5 rounded-xl border cursor-pointer transition ${
                      isSelected
                        ? "border-blue-500 bg-blue-500/10 shadow-md shadow-blue-500/10"
                        : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] mb-1.5">
                      <span className="font-mono text-slate-400">
                        {new Date(r.created_at).toLocaleDateString()}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                          r.status === "completed"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : r.status === "completed_partial"
                            ? "bg-amber-500/15 text-amber-300"
                            : "bg-blue-500/10 text-blue-400"
                        }`}
                      >
                        {r.status.replace("_", " ")}
                      </span>
                    </div>

                    <p className="text-xs font-medium text-slate-200 line-clamp-2">{r.question}</p>

                    <div className="flex items-center space-x-3 mt-2 text-[10px] text-slate-500 font-mono">
                      <span>Iterations: {r.research_iterations}</span>
                      <span>&bull;</span>
                      <span>Tool Calls: {r.tool_calls_used}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* New Research Run Modal */}
      {showNewRunModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => !isStartingRun && setShowNewRunModal(false)}
          />
          <div className="relative w-full max-w-xl bg-[#0a0f1d] border border-slate-800 rounded-2xl shadow-2xl p-6 z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Sparkles className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-bold text-white">Start New Agentic Research</h3>
              </div>
              <button
                onClick={() => setShowNewRunModal(false)}
                disabled={isStartingRun}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleStartRun} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2">
                  Research Question or Topic
                </label>
                <textarea
                  rows={3}
                  value={newRunQuestion}
                  onChange={(e) => setNewRunQuestion(e.target.value)}
                  placeholder="e.g. Research NVIDIA: evaluate datacenter revenue sustainability, Blackwell GPU roadmap, and antitrust risks"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition resize-none"
                  required
                />
              </div>

              {/* Preset Prompts */}
              <div>
                <span className="block text-[11px] font-semibold text-slate-400 mb-1.5">
                  Suggested Research Topics:
                </span>
                <div className="space-y-1.5">
                  {PRESET_RESEARCH_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setNewRunQuestion(prompt)}
                      className="w-full text-left p-2 rounded-lg bg-slate-900/40 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 text-[11px] text-slate-300 transition flex items-center justify-between group"
                    >
                      <span className="truncate pr-2">{prompt}</span>
                      <Zap className="h-3 w-3 text-blue-400 opacity-60 group-hover:opacity-100 shrink-0" />
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewRunModal(false)}
                  disabled={isStartingRun}
                  className="px-3.5 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isStartingRun || !newRunQuestion.trim()}
                  className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-lg shadow-blue-500/20 transition disabled:opacity-50"
                >
                  {isStartingRun ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Initiating...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-3.5 w-3.5" />
                      <span>Launch Research Run</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
