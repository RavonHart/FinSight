"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Brain,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  BarChart3,
  Loader2,
  ChevronDown,
  ChevronUp,
  Info,
  Layers,
  Target,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";
import {
  getQuestionnaire,
  submitAssessment,
  QuestionnaireItem,
  ProfileWithAssessment,
  createGoal,
} from "@/lib/profile";

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();

  const [questions, setQuestions] = useState<QuestionnaireItem[]>([]);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<string, any>>({
    investable_capital: 25000,
    monthly_contribution: 500,
    investment_horizon: "medium",
    primary_goal: "wealth_growth",
    experience_level: "intermediate",
    liquidity_requirement: "moderate",
    reaction_to_market_drop: "hold_steady",
    emergency_fund_coverage: "3_to_6_months",
    income_stability: "moderate",
  });

  const [isLoadingQuestions, setIsLoadingQuestions] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProfileWithAssessment | null>(null);
  const [showExplanation, setShowExplanation] = useState<boolean>(true);
  const [showHowDetermined, setShowHowDetermined] = useState<boolean>(false);

  // Quick goal form
  const [goalName, setGoalName] = useState<string>("Wealth Accumulation");
  const [goalAmount, setGoalAmount] = useState<string>("100000");
  const [goalDate, setGoalDate] = useState<string>("2030-12-31");
  const [goalSaved, setGoalSaved] = useState<boolean>(false);
  const [isSavingGoal, setIsSavingGoal] = useState<boolean>(false);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
      return;
    }

    async function loadData() {
      try {
        const qList = await getQuestionnaire();
        setQuestions(qList);
      } catch (err: any) {
        setError(err.message || "Failed to load questionnaire");
      } finally {
        setIsLoadingQuestions(false);
      }
    }

    if (user) {
      loadData();
    }
  }, [user, isAuthLoading, router]);

  if (isAuthLoading || isLoadingQuestions) {
    return (
      <div className="min-h-screen bg-[#090d16] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
        <p className="text-sm text-slate-400">Loading structured judgment questions...</p>
      </div>
    );
  }

  const currentQ = questions[currentStep];
  const progressPercent = questions.length > 0 ? Math.round(((currentStep + 1) / questions.length) * 100) : 0;

  const handleSelectOption = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleNumberChange = (questionId: string, value: string) => {
    const num = parseFloat(value);
    setAnswers((prev) => ({ ...prev, [questionId]: isNaN(num) ? 0 : num }));
  };

  const handleNext = () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await submitAssessment(answers);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Assessment evaluation failed. Please verify your inputs.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingGoal(true);
    try {
      await createGoal({
        name: goalName,
        type: "general",
        target_amount: goalAmount,
        target_date: goalDate,
        priority: 1,
      });
      setGoalSaved(true);
    } catch (err: any) {
      setError(err.message || "Failed to save initial goal");
    } finally {
      setIsSavingGoal(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
      {/* Top Bar */}
      <header className="border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/app/dashboard" className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">FinSight</span>
          </Link>
          <div className="flex items-center space-x-2 text-xs font-semibold px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Brain className="h-3.5 w-3.5" />
            <span>Jev Structured Judgment Layer</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-10">
        {/* If result is ready, show Result and "How was this determined" */}
        {result ? (
          <div className="space-y-8 animate-in fade-in-50 duration-500">
            {/* Header Banner */}
            <div className="p-8 rounded-3xl border border-blue-500/20 bg-gradient-to-b from-blue-950/20 via-slate-900/60 to-slate-950/80 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                <Brain className="h-48 w-48 text-blue-400" />
              </div>

              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold mb-4">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Profile Version {result.profile.profile_version} Established</span>
              </div>

              <h1 className="text-3xl font-extrabold text-white tracking-tight">
                Your AI-Calibrated Financial Profile
              </h1>
              <p className="mt-2 text-slate-300 text-sm max-w-2xl leading-relaxed">
                This structured assessment was synthesized through Jev System One questions, evaluating atomic risk and liquidity dimensions with calibrated certainty.
              </p>

              {/* Confidence Callout */}
              <div className="mt-6 flex flex-wrap items-center gap-4 pt-6 border-t border-slate-800/80">
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400">Confidence Score:</span>
                  <span className="text-sm font-bold text-white">
                    {Math.round(result.assessment.confidence * 100)}%
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400">Routing Action:</span>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wider ${
                    result.assessment.routing_action === "continue"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}>
                    {result.assessment.routing_action.replace(/_/g, " ")}
                  </span>
                </div>
              </div>
            </div>

            {/* Profile Core Attributes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
                <span className="text-xs text-slate-400 block font-medium">Risk Tolerance</span>
                <span className="text-xl font-bold text-blue-400 mt-1 block">
                  {result.profile.risk_tolerance}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">Psychological capacity for volatility</span>
              </div>

              <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
                <span className="text-xs text-slate-400 block font-medium">Risk Capacity</span>
                <span className="text-xl font-bold text-indigo-400 mt-1 block">
                  {result.profile.risk_capacity}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">Financial loss-absorption reserve</span>
              </div>

              <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
                <span className="text-xs text-slate-400 block font-medium">Liquidity Need</span>
                <span className="text-xl font-bold text-purple-400 mt-1 block">
                  {result.profile.liquidity_requirement}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">Cash access requirement</span>
              </div>

              <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
                <span className="text-xs text-slate-400 block font-medium">Horizon & Goals</span>
                <span className="text-xl font-bold text-emerald-400 mt-1 block capitalize">
                  {result.profile.investment_horizon}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">
                  ${Number(result.profile.investable_capital).toLocaleString()} deployed
                </span>
              </div>
            </div>

            {/* Structured Factor Breakdown ("How was this determined?") */}
            <div className="border border-slate-800 rounded-3xl bg-slate-900/30 overflow-hidden">
              <button
                onClick={() => setShowHowDetermined(!showHowDetermined)}
                className="w-full px-6 py-5 flex items-center justify-between hover:bg-slate-800/40 transition text-left"
              >
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                    <BarChart3 className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">How was this determined?</h3>
                    <p className="text-xs text-slate-400">
                      Inspect the atomic Jev questions and calibrated probability distributions
                    </p>
                  </div>
                </div>
                {showHowDetermined ? (
                  <ChevronUp className="h-5 w-5 text-slate-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-slate-400" />
                )}
              </button>

              {showHowDetermined && (
                <div className="p-6 pt-2 border-t border-slate-800/80 space-y-6">
                  <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                    <strong className="text-slate-200">Architectural Note:</strong> Jev does not act as an unconstrained generative advisor. Instead, it evaluates specific atomic decision dimensions with explicit calibration. Below are the structured probability vectors output by the judgment layer.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(result.assessment.jev_dimensions || {}).map(([dimKey, dim]) => (
                      <div key={dimKey} className="p-4 rounded-2xl border border-slate-800/80 bg-slate-950/40 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                            {dimKey.replace(/_/g, " ")}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono">
                            {Math.round(dim.confidence * 100)}% conf
                          </span>
                        </div>

                        {dim.choice_value && (
                          <div className="text-sm font-bold text-white">
                            Result: <span className="text-blue-400">{dim.choice_value}</span>
                          </div>
                        )}

                        {dim.probabilities && (
                          <div className="space-y-1.5 pt-2 border-t border-slate-800/60">
                            {Object.entries(dim.probabilities).map(([option, prob]) => (
                              <div key={option} className="space-y-1">
                                <div className="flex justify-between text-xs text-slate-400">
                                  <span>{option}</span>
                                  <span>{Math.round(prob * 100)}%</span>
                                </div>
                                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                                    style={{ width: `${Math.round(prob * 100)}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Next Steps: Add a Financial Goal */}
            <div className="p-6 rounded-3xl border border-slate-800 bg-slate-900/40 space-y-6">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <Target className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Define your Primary Financial Goal</h3>
                  <p className="text-xs text-slate-400">Anchor your research and portfolio simulations to a concrete target</p>
                </div>
              </div>

              {goalSaved ? (
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span>Primary goal saved successfully! You are ready to explore your workspace.</span>
                </div>
              ) : (
                <form onSubmit={handleAddGoal} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Goal Name</label>
                    <input
                      type="text"
                      value={goalName}
                      onChange={(e) => setGoalName(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Target Amount ($)</label>
                    <input
                      type="number"
                      value={goalAmount}
                      onChange={(e) => setGoalAmount(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Target Date</label>
                    <input
                      type="date"
                      value={goalDate}
                      onChange={(e) => setGoalDate(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                      required
                    />
                  </div>
                  <div className="md:col-span-3 flex justify-end">
                    <button
                      type="submit"
                      disabled={isSavingGoal}
                      className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition flex items-center space-x-1.5 shadow-lg shadow-emerald-500/20"
                    >
                      {isSavingGoal ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Target className="h-3.5 w-3.5" />}
                      <span>Save Goal</span>
                    </button>
                  </div>
                </form>
              )}
            </div>

            {/* Action Bar */}
            <div className="flex justify-between items-center pt-4">
              <button
                onClick={() => setResult(null)}
                className="text-xs text-slate-400 hover:text-slate-200 transition"
              >
                &larr; Retake Questionnaire
              </button>

              <Link
                href="/app/dashboard"
                className="px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold transition flex items-center space-x-2 shadow-lg shadow-blue-500/25"
              >
                <span>Proceed to FinSight Workspace</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        ) : (
          /* Questionnaire Wizard */
          <div className="space-y-6">
            {/* Header */}
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                <span>Question {currentStep + 1} of {questions.length}</span>
                <span>{progressPercent}% Complete</span>
              </div>
              <div className="h-1.5 w-full bg-slate-800/80 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Active Question Card */}
            {currentQ && (
              <div className="p-8 rounded-3xl border border-slate-800 bg-slate-900/40 space-y-6 shadow-xl relative">
                <div>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
                    {currentQ.category}
                  </span>
                  <h2 className="text-2xl font-bold text-white mt-3">{currentQ.title}</h2>
                  <p className="text-sm text-slate-400 mt-1">{currentQ.description}</p>
                </div>

                {/* Input Controls */}
                {currentQ.input_type === "select" && currentQ.options ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    {currentQ.options.map((opt) => {
                      const isSelected = answers[currentQ.id] === opt.value;
                      return (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => handleSelectOption(currentQ.id, opt.value)}
                          className={`p-4 rounded-2xl text-left border transition relative flex flex-col justify-between ${
                            isSelected
                              ? "bg-blue-600/10 border-blue-500 text-white shadow-lg shadow-blue-500/10"
                              : "bg-slate-950/40 border-slate-800/80 text-slate-300 hover:border-slate-700 hover:bg-slate-900/60"
                          }`}
                        >
                          <div>
                            <div className="font-semibold text-sm">{opt.label}</div>
                            {opt.description && (
                              <div className="text-xs text-slate-500 mt-1 leading-relaxed">
                                {opt.description}
                              </div>
                            )}
                          </div>
                          {isSelected && (
                            <div className="mt-2 flex items-center space-x-1 text-xs text-blue-400 font-medium">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span>Selected</span>
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <div className="max-w-md pt-2">
                    <label className="text-xs text-slate-400 block mb-1.5">
                      Amount in USD ({currentQ.unit || "$"})
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-sm font-semibold">
                        $
                      </span>
                      <input
                        type="number"
                        min={currentQ.min_value || 0}
                        max={currentQ.max_value || 10000000}
                        step={currentQ.step || 100}
                        value={answers[currentQ.id] || ""}
                        onChange={(e) => handleNumberChange(currentQ.id, e.target.value)}
                        className="w-full pl-8 pr-4 py-3 bg-slate-950 border border-slate-800 rounded-2xl text-white font-medium focus:outline-none focus:border-blue-500 text-base"
                      />
                    </div>
                  </div>
                )}

                {/* "Why this matters" Collapsible */}
                {currentQ.why_it_matters && (
                  <div className="pt-4 border-t border-slate-800/60">
                    <div className="p-4 rounded-2xl bg-slate-950/40 border border-slate-800/80 flex items-start space-x-3">
                      <Info className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
                      <div className="text-xs text-slate-400 leading-relaxed">
                        <strong className="text-slate-200">Why this matters: </strong>
                        {currentQ.why_it_matters}
                      </div>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
                    <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between items-center pt-2">
              <button
                type="button"
                onClick={handlePrev}
                disabled={currentStep === 0}
                className="px-5 py-2.5 rounded-xl border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 disabled:opacity-30 disabled:pointer-events-none transition flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Previous</span>
              </button>

              {currentStep === questions.length - 1 ? (
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold transition flex items-center space-x-2 shadow-lg shadow-blue-500/25 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Synthesizing Profile...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      <span>Submit & Synthesize Profile</span>
                    </>
                  )}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleNext}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition flex items-center space-x-2 shadow-lg shadow-blue-500/20"
                >
                  <span>Next</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
