"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
  Award,
  Layers,
  Search,
  Filter,
  BarChart3,
  TrendingUp,
  Brain,
  HelpCircle,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";
import {
  listLearningModules,
  getLearningSummary,
  LearningModuleSummary,
  LearningSummary,
} from "@/lib/learning";

const CATEGORIES = [
  "All",
  "Basics",
  "Risk",
  "Portfolio",
  "Stocks",
  "Funds",
  "Financial Statements",
  "Valuation",
  "Macroeconomics",
];

const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Basics: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  Risk: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  Portfolio: { bg: "bg-indigo-500/10", text: "text-indigo-400", border: "border-indigo-500/30" },
  Stocks: { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/30" },
  Funds: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/30" },
  "Financial Statements": { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
  Valuation: { bg: "bg-rose-500/10", text: "text-rose-400", border: "border-rose-500/30" },
  Macroeconomics: { bg: "bg-teal-500/10", text: "text-teal-400", border: "border-teal-500/30" },
};

export default function LearningHubPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();

  const [modules, setModules] = useState<LearningModuleSummary[]>([]);
  const [summary, setSummary] = useState<LearningSummary | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [mods, sum] = await Promise.all([
        listLearningModules(selectedCategory, selectedDifficulty),
        getLearningSummary().catch(() => null),
      ]);
      setModules(mods);
      if (sum) setSummary(sum);
    } catch (err: any) {
      setError(err.message || "Failed to load curriculum");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user, selectedCategory, selectedDifficulty]);

  const filteredModules = modules.filter((m) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return m.title.toLowerCase().includes(q) || m.summary.toLowerCase().includes(q);
  });

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              href="/app/dashboard"
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Return to Dashboard"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <BookOpen className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-wide">Financial Learning Hub</h1>
                <p className="text-xs text-slate-400">Phase 8 • Interactive Curriculum & AI Tutor</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              href="/app/simulation"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 transition flex items-center space-x-1.5"
            >
              <TrendingUp className="h-3.5 w-3.5 text-cyan-400" />
              <span>Simulations</span>
            </Link>
            <Link
              href="/app/research"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 transition flex items-center space-x-1.5"
            >
              <Brain className="h-3.5 w-3.5 text-indigo-400" />
              <span>Research</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Progress & Hero Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/50 to-amber-950/20 p-6 md:p-8">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-xl">
              <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Institutional-Grade Financial Literacy</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Master Investment Theory &amp; Market Dynamics
              </h2>
              <p className="text-sm text-slate-400 leading-relaxed">
                Explore 8 foundational financial domains—from exponential compounding and volatility drag to
                intrinsic DCF valuation. Learn with interactive visualizers, take comprehension quizzes, and get
                socratic guidance from your AI Financial Tutor.
              </p>
            </div>

            {/* Overall Progress Stats */}
            {summary && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 min-w-[280px]">
                <div className="text-center p-2 border-r border-slate-800/80">
                  <div className="text-2xl font-black text-amber-400">
                    {summary.overall_completion_pct}%
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Mastery Rate</div>
                </div>
                <div className="text-center p-2 border-r border-slate-800/80">
                  <div className="text-2xl font-black text-emerald-400">
                    {summary.completed_modules}/{summary.total_modules}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Completed</div>
                </div>
                <div className="text-center p-2 col-span-2 sm:col-span-1">
                  <div className="text-2xl font-black text-cyan-400">
                    {summary.average_quiz_score ? `${summary.average_quiz_score}%` : "—"}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Avg Score</div>
                </div>
              </div>
            )}
          </div>

          {/* Progress bar line */}
          {summary && (
            <div className="mt-6 w-full bg-slate-800/60 h-2 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-amber-500 via-emerald-500 to-cyan-500 h-full transition-all duration-700 ease-out"
                style={{ width: `${Number(summary.overall_completion_pct) || 0}%` }}
              />
            </div>
          )}
        </div>

        {/* Filter & Search Bar */}
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* Category pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
              {CATEGORIES.map((cat) => {
                const isActive = selectedCategory === cat;
                return (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`whitespace-nowrap px-3.5 py-1.5 rounded-xl text-xs font-medium transition ${
                      isActive
                        ? "bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/20"
                        : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800/80 border border-slate-800/60"
                    }`}
                  >
                    {cat}
                  </button>
                );
              })}
            </div>

            {/* Difficulty & Search */}
            <div className="flex items-center gap-3">
              <div className="relative flex-1 sm:w-48">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search concepts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
                />
              </div>

              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="bg-slate-900/80 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-amber-500/50"
              >
                <option value="all">All Difficulties</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </div>
        </div>

        {/* Module Cards Grid */}
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="h-6 w-6 animate-spin text-amber-400" />
            <p className="text-sm">Loading curriculum modules...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-sm">
            {error}
          </div>
        ) : filteredModules.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl text-slate-500">
            No learning modules found matching your filters.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredModules.map((mod) => {
              const catTheme = CATEGORY_COLORS[mod.category] || {
                bg: "bg-slate-800",
                text: "text-slate-300",
                border: "border-slate-700",
              };
              const progNum = Number(mod.progress) || 0;

              return (
                <div
                  key={mod.id}
                  className="group relative flex flex-col justify-between rounded-2xl border border-slate-800/90 bg-slate-900/40 p-6 hover:bg-slate-900/70 hover:border-slate-700 transition duration-200"
                >
                  <div className="space-y-4">
                    {/* Header: Category Badge + Difficulty */}
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${catTheme.bg} ${catTheme.text} ${catTheme.border}`}
                      >
                        {mod.category}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] uppercase tracking-wider text-slate-400">
                          {mod.difficulty}
                        </span>
                        {mod.completed && (
                          <div className="flex items-center space-x-1 text-emerald-400 text-xs font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            <span>Passed</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Title & Summary */}
                    <div>
                      <h3 className="text-base font-bold text-white group-hover:text-amber-300 transition">
                        {mod.title}
                      </h3>
                      <p className="mt-2 text-xs text-slate-400 line-clamp-3 leading-relaxed">
                        {mod.summary}
                      </p>
                    </div>
                  </div>

                  {/* Footer & Progress */}
                  <div className="mt-6 pt-4 border-t border-slate-800/80 space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Completion</span>
                      <span className="font-semibold text-white">{progNum}%</span>
                    </div>

                    {/* Progress track */}
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          mod.completed ? "bg-emerald-400" : "bg-amber-400"
                        }`}
                        style={{ width: `${progNum}%` }}
                      />
                    </div>

                    {/* Action link */}
                    <Link
                      href={`/app/learning/${mod.slug}`}
                      className="w-full mt-2 inline-flex items-center justify-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition bg-slate-800/80 hover:bg-amber-500 hover:text-slate-950 text-slate-200 border border-slate-700/60"
                    >
                      <span>
                        {mod.completed
                          ? "Review & Retake Quiz"
                          : progNum > 0
                          ? "Continue Lesson"
                          : "Start Lesson"}
                      </span>
                      <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
