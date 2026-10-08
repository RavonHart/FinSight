"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  Brain,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sparkles,
  Sliders,
  DollarSign,
  TrendingUp,
  Percent,
  Send,
  MessageSquare,
  AlertTriangle,
  RotateCcw,
  Award,
  Layers,
  Info,
  Clock,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";
import {
  getLearningModule,
  submitQuiz,
  getQuizHistory,
  askAITutor,
  LearningModuleDetail,
  QuizAttemptResponse,
  AITutorResponse,
} from "@/lib/learning";

export default function LearningLessonPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params?.slug as string;
  const { user, isLoading: authLoading } = useAuth();

  // Module state
  const [module, setModule] = useState<LearningModuleDetail | null>(null);
  const [activeTab, setActiveTab] = useState<"lesson" | "tutor" | "quiz">("lesson");
  const [explanationMode, setExplanationMode] = useState<"standard" | "eli5" | "quant">("standard");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Quiz state
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [isSubmittingQuiz, setIsSubmittingQuiz] = useState<boolean>(false);
  const [quizResult, setQuizResult] = useState<QuizAttemptResponse | null>(null);
  const [quizHistory, setQuizHistory] = useState<QuizAttemptResponse[]>([]);

  // AI Tutor state
  const [tutorQuery, setTutorQuery] = useState<string>("");
  const [tutorMode, setTutorMode] = useState<"clarify" | "eli5" | "quant" | "profile_context" | "quiz_help">("clarify");
  const [isTutorLoading, setIsTutorLoading] = useState<boolean>(false);
  const [chatMessages, setChatMessages] = useState<
    Array<{
      sender: "user" | "tutor";
      text: string;
      mode?: string;
      concepts?: string[];
      followups?: string[];
      profileApplied?: boolean;
      isAdvisoryRefusal?: boolean;
    }>
  >([]);

  // Interactive sandbox state (compounding & fee drag calculator)
  const [sandboxMonthly, setSandboxMonthly] = useState<number>(500);
  const [sandboxYears, setSandboxYears] = useState<number>(20);
  const [sandboxReturn, setSandboxReturn] = useState<number>(8.0);
  const [sandboxFee, setSandboxFee] = useState<number>(0.25);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const loadModuleData = async () => {
    if (!slug) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await getLearningModule(slug);
      setModule(data);

      // Load quiz history
      const history = await getQuizHistory(slug).catch(() => []);
      setQuizHistory(history);
      if (history.length > 0) {
        setQuizResult(history[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load lesson");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user && slug) {
      loadModuleData();
    }
  }, [user, slug]);

  // Handle quiz submission
  const handleQuizSubmit = async () => {
    if (!module || !slug) return;
    if (Object.keys(selectedAnswers).length < module.quiz_questions.length) {
      alert("Please answer all questions before submitting.");
      return;
    }

    setIsSubmittingQuiz(true);
    try {
      const result = await submitQuiz(slug, selectedAnswers);
      setQuizResult(result);
      setQuizHistory((prev) => [result, ...prev]);
      // Update local module progress
      setModule((prev) =>
        prev
          ? {
              ...prev,
              completed: result.passed || prev.completed,
              progress: result.passed ? 100 : Math.max(Number(prev.progress), 75),
              best_score: Math.max(Number(prev.best_score || 0), Number(result.score)),
            }
          : null
      );
    } catch (err: any) {
      alert(err.message || "Quiz submission failed");
    } finally {
      setIsSubmittingQuiz(false);
    }
  };

  // Handle AI Tutor query
  const handleAskTutor = async (queryText?: string, modeOverride?: any) => {
    const q = queryText || tutorQuery;
    const m = modeOverride || tutorMode;
    if (!q.trim() || !slug) return;

    // Add user message
    setChatMessages((prev) => [...prev, { sender: "user", text: q }]);
    if (!queryText) setTutorQuery("");
    setIsTutorLoading(true);

    try {
      const res: AITutorResponse = await askAITutor(slug, q, m);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "tutor",
          text: res.explanation,
          mode: res.mode,
          concepts: res.concepts_referenced,
          followups: res.suggested_followups,
          profileApplied: res.profile_context_applied,
          isAdvisoryRefusal: res.is_advisory_refusal,
        },
      ]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "tutor",
          text: `⚠️ Error from AI Tutor: ${err.message || "Could not retrieve response."}`,
        },
      ]);
    } finally {
      setIsTutorLoading(false);
    }
  };

  // Calculate sandbox results
  const computeSandbox = () => {
    const rNet = (sandboxReturn - sandboxFee) / 100 / 12;
    const rGross = sandboxReturn / 100 / 12;
    const nMonths = sandboxYears * 12;

    const netBalance =
      sandboxMonthly * ((Math.pow(1 + rNet, nMonths) - 1) / (rNet || 0.0001));
    const grossBalance =
      sandboxMonthly * ((Math.pow(1 + rGross, nMonths) - 1) / (rGross || 0.0001));
    const totalContributed = sandboxMonthly * nMonths;
    const feeLoss = Math.max(0, grossBalance - netBalance);

    return {
      netBalance: Math.round(netBalance),
      grossBalance: Math.round(grossBalance),
      totalContributed,
      feeLoss: Math.round(feeLoss),
    };
  };

  const sandboxCalc = computeSandbox();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-amber-400" />
        <p className="text-sm text-slate-400">Loading interactive lesson...</p>
      </div>
    );
  }

  if (error || !module) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 p-8 flex flex-col items-center justify-center space-y-4">
        <div className="p-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-300 max-w-md text-center">
          <p className="font-bold">Error loading module</p>
          <p className="text-xs mt-1 text-slate-400">{error || "Module not found"}</p>
          <Link
            href="/app/learning"
            className="mt-4 inline-flex items-center space-x-1.5 text-xs font-semibold text-amber-400 hover:underline"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Return to Learning Hub</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              href="/app/learning"
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Back to Learning Hub"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {module.category}
                </span>
                <span className="text-[10px] uppercase font-bold text-slate-400">
                  {module.difficulty}
                </span>
                {module.completed && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1">
                    <CheckCircle2 className="h-3 w-3" />
                    <span>Mastered</span>
                  </span>
                )}
              </div>
              <h1 className="text-sm sm:text-base font-extrabold text-white truncate max-w-sm sm:max-w-md">
                {module.title}
              </h1>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center space-x-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab("lesson")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                activeTab === "lesson"
                  ? "bg-amber-500 text-slate-950 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Lesson</span>
            </button>
            <button
              onClick={() => setActiveTab("tutor")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                activeTab === "tutor"
                  ? "bg-amber-500 text-slate-950 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Brain className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">AI Tutor</span>
            </button>
            <button
              onClick={() => setActiveTab("quiz")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                activeTab === "quiz"
                  ? "bg-amber-500 text-slate-950 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Award className="h-3.5 w-3.5" />
              <span>Quiz</span>
              {module.best_score && (
                <span className="ml-1 text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-amber-300">
                  {module.best_score}%
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* TAB 1: LESSON */}
        {activeTab === "lesson" && (
          <div className="space-y-8">
            {/* "Explain This Differently" Pill Switcher (§29) */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl border border-slate-800 bg-slate-900/40">
              <div className="flex items-center space-x-2 text-xs text-slate-400">
                <Sparkles className="h-4 w-4 text-amber-400" />
                <span className="font-semibold text-white">Pedagogical Lens:</span>
                <span>Choose how you prefer this concept explained</span>
              </div>
              <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800/80">
                <button
                  onClick={() => setExplanationMode("standard")}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
                    explanationMode === "standard"
                      ? "bg-amber-500 text-slate-950 font-bold"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Core Concept
                </button>
                <button
                  onClick={() => setExplanationMode("eli5")}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
                    explanationMode === "eli5"
                      ? "bg-amber-500 text-slate-950 font-bold"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  ELI5 / Analogy
                </button>
                <button
                  onClick={() => setExplanationMode("quant")}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
                    explanationMode === "quant"
                      ? "bg-amber-500 text-slate-950 font-bold"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Quantitative Rigor
                </button>
              </div>
            </div>

            {/* Explanation Content Box */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/30 p-6 md:p-8 space-y-6">
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
                  <BookOpen className="h-4 w-4" />
                  <span>
                    {explanationMode === "standard" && "Foundational Investment Theory"}
                    {explanationMode === "eli5" && "Simplified Mental Model (ELI5)"}
                    {explanationMode === "quant" && "Mathematical & Quantitative Formulation"}
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white leading-snug">
                  {module.title}
                </h2>
                <div className="text-sm text-slate-300 leading-relaxed space-y-4 whitespace-pre-line">
                  {explanationMode === "standard" && module.concept}
                  {explanationMode === "eli5" && module.eli5}
                  {explanationMode === "quant" && module.quant}
                </div>
              </div>

              {/* Real World Example */}
              <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-5 space-y-2">
                <div className="flex items-center space-x-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
                  <TrendingUp className="h-4 w-4" />
                  <span>Institutional Case Study &amp; Historical Context</span>
                </div>
                <p className="text-xs sm:text-sm text-cyan-100/90 leading-relaxed whitespace-pre-line">
                  {module.example}
                </p>
              </div>

              {/* Key Takeaways */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Core Principles to Remember
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {module.key_takeaways.map((item, idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Embedded Interactive Concept Sandbox (§29 Visual Explanation) */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 md:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
                    <Sliders className="h-4 w-4" />
                    <span>Interactive Concept Visualizer</span>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1">
                    Compound Growth &amp; Expense Drag Simulator
                  </h3>
                </div>
                <div className="text-xs text-slate-400">
                  Instant mathematical feedback
                </div>
              </div>

              {/* Sliders Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Monthly Addition</span>
                    <span className="font-semibold text-white">${sandboxMonthly}</span>
                  </div>
                  <input
                    type="range"
                    min="100"
                    max="3000"
                    step="100"
                    value={sandboxMonthly}
                    onChange={(e) => setSandboxMonthly(Number(e.target.value))}
                    className="w-full accent-amber-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Horizon (Years)</span>
                    <span className="font-semibold text-white">{sandboxYears} yrs</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="40"
                    step="1"
                    value={sandboxYears}
                    onChange={(e) => setSandboxYears(Number(e.target.value))}
                    className="w-full accent-amber-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Gross Return</span>
                    <span className="font-semibold text-white">{sandboxReturn}%</span>
                  </div>
                  <input
                    type="range"
                    min="3.0"
                    max="14.0"
                    step="0.5"
                    value={sandboxReturn}
                    onChange={(e) => setSandboxReturn(Number(e.target.value))}
                    className="w-full accent-emerald-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Expense Fee Drag</span>
                    <span className="font-semibold text-rose-400">{sandboxFee}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.05"
                    max="2.5"
                    step="0.05"
                    value={sandboxFee}
                    onChange={(e) => setSandboxFee(Number(e.target.value))}
                    className="w-full accent-rose-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                  />
                </div>
              </div>

              {/* Dynamic Math Results Box */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 bg-slate-950/80 p-5 rounded-xl border border-slate-800/80">
                <div className="text-center sm:text-left">
                  <span className="text-[11px] text-slate-400">Total Out-of-Pocket</span>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">
                    ${sandboxCalc.totalContributed.toLocaleString()}
                  </div>
                </div>
                <div className="text-center sm:text-left">
                  <span className="text-[11px] text-slate-400">Gross Wealth (0% Fee)</span>
                  <div className="text-lg font-bold text-cyan-400 mt-0.5">
                    ${sandboxCalc.grossBalance.toLocaleString()}
                  </div>
                </div>
                <div className="text-center sm:text-left">
                  <span className="text-[11px] text-slate-400">Net Ending Balance</span>
                  <div className="text-lg font-bold text-emerald-400 mt-0.5">
                    ${sandboxCalc.netBalance.toLocaleString()}
                  </div>
                </div>
                <div className="text-center sm:text-left">
                  <span className="text-[11px] text-rose-400">Cumulative Fee Drag Loss</span>
                  <div className="text-lg font-bold text-rose-400 mt-0.5">
                    -${sandboxCalc.feeLoss.toLocaleString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Action Footer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
              <div className="flex items-center space-x-3">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                <span className="text-xs text-slate-300">
                  Ready to test your comprehension or ask the AI Tutor questions?
                </span>
              </div>
              <div className="flex items-center space-x-3 w-full sm:w-auto">
                <button
                  onClick={() => setActiveTab("tutor")}
                  className="flex-1 sm:flex-initial px-4 py-2 rounded-xl text-xs font-bold border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 transition flex items-center justify-center space-x-1.5"
                >
                  <Brain className="h-4 w-4 text-amber-400" />
                  <span>Ask AI Tutor</span>
                </button>
                <button
                  onClick={() => setActiveTab("quiz")}
                  className="flex-1 sm:flex-initial px-5 py-2 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition flex items-center justify-center space-x-1.5 shadow-md shadow-amber-500/20"
                >
                  <Award className="h-4 w-4" />
                  <span>Take Knowledge Quiz</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: AI TUTOR */}
        {activeTab === "tutor" && (
          <div className="space-y-6">
            {/* Tutor Controls Header */}
            <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <Brain className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">
                      FinSight AI Financial Tutor
                    </h3>
                    <p className="text-xs text-slate-400">
                      Grounded in {module.title} • Personalized with your risk profile
                    </p>
                  </div>
                </div>

                {/* Tutoring Style Mode selector */}
                <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800/80">
                  <button
                    onClick={() => setTutorMode("clarify")}
                    className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
                      tutorMode === "clarify"
                        ? "bg-amber-500 text-slate-950 font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Clarify
                  </button>
                  <button
                    onClick={() => setTutorMode("eli5")}
                    className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
                      tutorMode === "eli5"
                        ? "bg-amber-500 text-slate-950 font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    ELI5
                  </button>
                  <button
                    onClick={() => setTutorMode("quant")}
                    className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
                      tutorMode === "quant"
                        ? "bg-amber-500 text-slate-950 font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Quant
                  </button>
                  <button
                    onClick={() => setTutorMode("profile_context")}
                    className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
                      tutorMode === "profile_context"
                        ? "bg-amber-500 text-slate-950 font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Profile Lens
                  </button>
                </div>
              </div>

              {/* Quick Prompts Chips */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
                <span className="text-[11px] text-slate-500 shrink-0 font-medium">Quick Prompts:</span>
                {[
                  `How does ${module.title} protect my wealth?`,
                  "Explain this like I'm 5 with an analogy",
                  "What is the mathematical equation?",
                  "How does this relate to my risk profile?",
                  "What is the biggest rookie mistake?",
                ].map((promptText, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAskTutor(promptText)}
                    className="whitespace-nowrap px-3 py-1 rounded-lg text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition"
                  >
                    {promptText}
                  </button>
                ))}
              </div>
            </div>

            {/* Conversation Window */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6 min-h-[380px] flex flex-col justify-between space-y-6">
              {chatMessages.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-3">
                  <div className="h-12 w-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                    <MessageSquare className="h-6 w-6" />
                  </div>
                  <h4 className="text-base font-bold text-white">Ask your AI Financial Tutor</h4>
                  <p className="text-xs text-slate-400 max-w-md leading-relaxed">
                    Have questions about {module.title}? Select a quick prompt above or type your
                    question below to receive socratic explanations, numerical proofs, or personal
                    risk alignment guidance.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {chatMessages.map((msg, index) => (
                    <div
                      key={index}
                      className={`flex flex-col ${
                        msg.sender === "user" ? "items-end" : "items-start"
                      }`}
                    >
                      <div
                        className={`max-w-2xl rounded-2xl p-4 text-xs sm:text-sm leading-relaxed ${
                          msg.sender === "user"
                            ? "bg-amber-500 text-slate-950 font-medium"
                            : "bg-slate-900 border border-slate-800 text-slate-200"
                        }`}
                      >
                        {msg.sender === "tutor" && msg.isAdvisoryRefusal && (
                          <div className="mb-3 inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-amber-500/15 text-amber-300 border border-amber-500/30 text-xs font-bold">
                            <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                            <span>Advisory Boundary Intercepted (§32, §69)</span>
                          </div>
                        )}
                        <div className="whitespace-pre-line">{msg.text}</div>

                        {/* Concepts & Follow-ups for Tutor messages */}
                        {msg.sender === "tutor" && msg.concepts && (
                          <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap gap-1.5">
                            {msg.concepts.map((c, i) => (
                              <span
                                key={i}
                                className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-amber-300 border border-slate-700"
                              >
                                {c}
                              </span>
                            ))}
                          </div>
                        )}

                        {msg.sender === "tutor" && msg.followups && msg.followups.length > 0 && (
                          <div className="mt-3 pt-2 space-y-1">
                            <span className="text-[10px] text-slate-500 font-semibold uppercase">
                              Suggested Follow-ups:
                            </span>
                            <div className="flex flex-wrap gap-1.5 mt-1">
                              {msg.followups.map((f, fi) => (
                                <button
                                  key={fi}
                                  onClick={() => handleAskTutor(f)}
                                  className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-cyan-300 border border-cyan-500/20 transition text-left"
                                >
                                  {f}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {isTutorLoading && (
                    <div className="flex items-center space-x-2 text-xs text-amber-400 bg-slate-900/60 p-3 rounded-xl border border-slate-800 w-fit">
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>AI Tutor is analyzing curriculum and formulating response...</span>
                    </div>
                  )}
                </div>
              )}

              {/* Chat Input Box */}
              <div className="pt-4 border-t border-slate-800/80 space-y-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={tutorQuery}
                    onChange={(e) => setTutorQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAskTutor()}
                    placeholder={`Ask anything about ${module.title}...`}
                    disabled={isTutorLoading}
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
                  />
                  <button
                    onClick={() => handleAskTutor()}
                    disabled={isTutorLoading || !tutorQuery.trim()}
                    className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">Ask</span>
                  </button>
                </div>
                <div className="text-[10px] text-slate-500 flex items-center space-x-1">
                  <ShieldCheck className="h-3 w-3 text-slate-500" />
                  <span>
                    FinSight AI Tutor is educational (§32); not individualized financial advice.
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: QUIZ */}
        {activeTab === "quiz" && (
          <div className="space-y-6">
            {/* Quiz Banner */}
            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="inline-flex items-center space-x-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
                  <Award className="h-4 w-4" />
                  <span>Comprehension Knowledge Check</span>
                </div>
                <h3 className="text-xl font-bold text-white mt-1">
                  {module.title} Quiz
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Pass with 70% or higher to mark this module as completed on your dashboard.
                </p>
              </div>

              {quizResult && (
                <div
                  className={`p-4 rounded-xl border text-center min-w-[160px] ${
                    quizResult.passed
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                  }`}
                >
                  <div className="text-2xl font-black">{quizResult.score}%</div>
                  <div className="text-xs font-bold mt-0.5">
                    {quizResult.passed ? "Passed ✓" : "Needs Review"}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    {quizResult.correct_count} of {quizResult.total_questions} correct
                  </div>
                </div>
              )}
            </div>

            {/* Questions Form */}
            <div className="space-y-6">
              {module.quiz_questions.map((q, qIndex) => {
                const feedbackItem = quizResult?.feedback.find((f) => f.id === q.id);
                const selectedIdx = selectedAnswers[q.id];

                return (
                  <div
                    key={q.id}
                    className={`rounded-2xl border p-6 space-y-4 transition ${
                      feedbackItem
                        ? feedbackItem.is_correct
                          ? "border-emerald-500/40 bg-emerald-950/10"
                          : "border-rose-500/40 bg-rose-950/10"
                        : "border-slate-800 bg-slate-900/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-amber-400">
                          Question {qIndex + 1} of {module.quiz_questions.length}
                        </span>
                        <h4 className="text-sm sm:text-base font-semibold text-white leading-snug">
                          {q.question}
                        </h4>
                      </div>

                      {feedbackItem && (
                        <div className="shrink-0">
                          {feedbackItem.is_correct ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span>Correct</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                              <XCircle className="h-3.5 w-3.5" />
                              <span>Incorrect</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Options */}
                    <div className="space-y-2 pt-2">
                      {q.options.map((optionText, optIdx) => {
                        const isChosen = selectedIdx === optIdx;
                        let optionStyle = "border-slate-800 bg-slate-950/60 hover:bg-slate-800/60 text-slate-300";

                        if (feedbackItem) {
                          if (optIdx === feedbackItem.correct_index) {
                            optionStyle = "border-emerald-500 bg-emerald-500/10 text-emerald-300 font-semibold";
                          } else if (isChosen && !feedbackItem.is_correct) {
                            optionStyle = "border-rose-500 bg-rose-500/10 text-rose-300";
                          } else {
                            optionStyle = "border-slate-800 bg-slate-950/40 opacity-60 text-slate-400";
                          }
                        } else if (isChosen) {
                          optionStyle = "border-amber-500 bg-amber-500/10 text-white font-semibold";
                        }

                        return (
                          <button
                            key={optIdx}
                            type="button"
                            onClick={() =>
                              setSelectedAnswers((prev) => ({ ...prev, [q.id]: optIdx }))
                            }
                            disabled={isSubmittingQuiz}
                            className={`w-full text-left p-3.5 rounded-xl border text-xs sm:text-sm flex items-center space-x-3 transition ${optionStyle}`}
                          >
                            <span
                              className={`h-6 w-6 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 border ${
                                isChosen
                                  ? "border-amber-400 bg-amber-500 text-slate-950"
                                  : "border-slate-700 bg-slate-900 text-slate-400"
                              }`}
                            >
                              {String.fromCharCode(65 + optIdx)}
                            </span>
                            <span className="flex-1">{optionText}</span>
                          </button>
                        );
                      })}
                    </div>

                    {/* Explanation feedback */}
                    {feedbackItem && (
                      <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
                        <span className="font-bold text-amber-400">Explanation: </span>
                        {feedbackItem.explanation}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Quiz Submit Bar */}
            <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-400">
                {Object.keys(selectedAnswers).length} of {module.quiz_questions.length} answered
              </div>
              <div className="flex items-center space-x-3 w-full sm:w-auto">
                {quizResult && (
                  <button
                    onClick={() => {
                      setSelectedAnswers({});
                      setQuizResult(null);
                    }}
                    className="flex-1 sm:flex-initial px-4 py-2.5 rounded-xl text-xs font-bold border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 transition flex items-center justify-center space-x-1.5"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Reset &amp; Retake</span>
                  </button>
                )}
                <button
                  onClick={handleQuizSubmit}
                  disabled={
                    isSubmittingQuiz ||
                    Object.keys(selectedAnswers).length < module.quiz_questions.length
                  }
                  className="flex-1 sm:flex-initial px-6 py-2.5 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center space-x-2 shadow-md shadow-amber-500/20"
                >
                  {isSubmittingQuiz ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Grading Answers...</span>
                    </>
                  ) : (
                    <>
                      <Award className="h-4 w-4" />
                      <span>Submit Quiz</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
