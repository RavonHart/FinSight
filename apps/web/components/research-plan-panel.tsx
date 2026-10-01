"use client";

import React from "react";
import {
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
  Brain,
  Shield,
  TrendingUp,
  Cpu,
  BarChart2,
  Scale,
  Activity,
  Layers,
} from "lucide-react";
import { ResearchTask, JevEvaluation } from "@/lib/research";

interface ResearchPlanPanelProps {
  tasks: ResearchTask[];
  jevEvaluations: JevEvaluation[];
  runStatus: string;
  iterations: number;
  toolCalls: number;
  activeStep?: string | null;
}

const DEFAULT_PIPELINE_STEPS = [
  { type: "planning", title: "Planner & Hypothesis Formulator", agent: "PlanningAgent" },
  { type: "financial_analysis", title: "Financial Metrics & Valuations", agent: "FinancialAgent" },
  { type: "market_analysis", title: "Competitive & Industry Analysis", agent: "MarketAgent" },
  { type: "news_analysis", title: "News, Catalysts & Filings", agent: "NewsAgent" },
  { type: "evidence_validation", title: "Evidence Extraction & Vector Embeddings", agent: "ValidationAgent" },
  { type: "jev_analysis", title: "Jev System One Calibrated Judgments", agent: "JevSystemOne" },
  { type: "synthesis", title: "Report Synthesis & Claim Grounding", agent: "SynthesisAgent" },
];

export const ResearchPlanPanel: React.FC<ResearchPlanPanelProps> = ({
  tasks,
  jevEvaluations,
  runStatus,
  iterations,
  toolCalls,
  activeStep,
}) => {
  // Map pipeline step status accurately from tasks, activeStep, and runStatus
  const getStepStatus = (stepType: string, stepIndex: number) => {
    // 1. Terminal completed states mark all steps completed
    if (runStatus === "completed" || runStatus === "completed_partial") {
      return "completed";
    }

    if (runStatus === "failed") {
      return "failed";
    }

    // 2. Check direct matching task from backend
    const matchingTask = tasks.find(
      (t) => t.task_type === stepType || t.title.toLowerCase().includes(stepType)
    );
    if (matchingTask && matchingTask.status) {
      return matchingTask.status;
    }

    // 3. Live activeStep tracking from SSE
    if (activeStep) {
      const activeIdx = DEFAULT_PIPELINE_STEPS.findIndex((s) => s.type === activeStep);
      if (activeIdx !== -1) {
        if (stepIndex < activeIdx) return "completed";
        if (stepIndex === activeIdx) return "running";
        return "pending";
      }
    }

    // 4. Fallback for running status
    if (runStatus === "running") {
      const completedTasks = tasks.filter((t) => t.status === "completed").length;
      if (stepIndex < completedTasks) return "completed";
      if (stepIndex === completedTasks) return "running";
      return "pending";
    }

    return "pending";
  };

  const getQuestionTitle = (qId: string) => {
    switch (qId) {
      case "evidence_sufficiency":
        return "Evidence Sufficiency";
      case "financial_strength":
        return "Financial Balance Sheet Strength";
      case "growth_outlook":
        return "Growth Outlook & Catalysts";
      case "competitive_pressure":
        return "Competitive Moat & Pressures";
      case "concentration_risk":
        return "Customer / Revenue Concentration";
      case "risk_level":
        return "Overall Risk Profile";
      default:
        return qId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0f1d] rounded-2xl border border-slate-800/80 shadow-xl overflow-hidden">
      {/* Panel Header */}
      <div className="px-5 py-4 border-b border-slate-800/80 bg-slate-900/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="h-7 w-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Layers className="h-4 w-4" />
            </div>
            <h2 className="text-sm font-bold text-white tracking-tight">Research Plan &amp; Tasks</h2>
          </div>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
              runStatus === "completed"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : runStatus === "completed_partial"
                ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                : runStatus === "running"
                ? "bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }`}
          >
            {runStatus.replace("_", " ").toUpperCase()}
          </span>
        </div>
      </div>

      <div className="flex-1 p-5 overflow-y-auto space-y-6">
        {/* Execution Pipeline Stepper */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <Activity className="h-3.5 w-3.5 text-blue-400" />
            <span>Agent Workflow Pipeline</span>
          </h3>

          <div className="space-y-2.5">
            {DEFAULT_PIPELINE_STEPS.map((step, idx) => {
              const status = getStepStatus(step.type, idx);

              return (
                <div
                  key={step.type}
                  className={`p-2.5 rounded-xl border transition flex items-center justify-between ${
                    status === "completed"
                      ? "bg-slate-900/40 border-slate-800/80 text-slate-200"
                      : status === "running"
                      ? "bg-blue-500/10 border-blue-500/40 text-blue-200 shadow-sm shadow-blue-500/10"
                      : "bg-slate-900/20 border-slate-800/40 text-slate-500"
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    {status === "completed" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    ) : status === "running" ? (
                      <Loader2 className="h-4 w-4 text-blue-400 animate-spin shrink-0" />
                    ) : (
                      <Circle className="h-4 w-4 text-slate-600 shrink-0" />
                    )}
                    <span className="text-xs font-medium">{step.title}</span>
                  </div>

                  <span className="text-[10px] font-mono text-slate-500 uppercase">{step.agent}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Jev System One Section (§13, §14) */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <Brain className="h-3.5 w-3.5 text-purple-400" />
              <span>Jev System One Judgments</span>
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono font-medium">
              Calibrated Probabilities
            </span>
          </div>

          {jevEvaluations.length > 0 ? (
            <div className="space-y-2.5">
              {jevEvaluations.map((evalItem) => {
                const confPercent = Math.round(evalItem.confidence * 100);
                const isHigh = evalItem.confidence >= 0.8;
                const isUnverified = evalItem.confidence < 0.5;

                return (
                  <div
                    key={evalItem.question_id}
                    className="p-3 rounded-xl border border-slate-800/80 bg-slate-900/50 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-200">
                        {getQuestionTitle(evalItem.question_id)}
                      </span>
                      <span
                        className={`text-[11px] font-bold font-mono px-1.5 py-0.5 rounded ${
                          isHigh
                            ? "bg-emerald-500/10 text-emerald-400"
                            : isUnverified
                            ? "bg-amber-500/10 text-amber-400"
                            : "bg-blue-500/10 text-blue-400"
                        }`}
                      >
                        {confPercent}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span className="capitalize text-slate-300 font-medium">
                        Verdict: {evalItem.choice_value.replace(/_/g, " ")}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {evalItem.model_version}
                      </span>
                    </div>

                    {/* Calibrated Confidence Bar */}
                    <div className="mt-2 w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isHigh ? "bg-emerald-500" : isUnverified ? "bg-amber-500" : "bg-blue-500"
                        }`}
                        style={{ width: `${confPercent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-500">
              <Brain className="h-6 w-6 text-slate-600 mx-auto mb-2" />
              <span>Jev judgments evaluate evidence after research tasks finish.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
