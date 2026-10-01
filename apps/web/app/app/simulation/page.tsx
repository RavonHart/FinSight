"use client";

import React, { useState, useEffect, useId } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  ArrowLeft,
  Sliders,
  DollarSign,
  Calendar,
  Percent,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle2,
  Info,
  Layers,
  ShieldCheck,
  Briefcase,
  History,
  FileSpreadsheet,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";
import { listPortfolios, getPortfolioAnalytics, Portfolio } from "@/lib/portfolio";
import {
  createSimulation,
  listSimulations,
  SimulationRequest,
  SimulationRun,
  SimulationResultJson,
  ScenarioResult,
} from "@/lib/simulation";

export default function SimulationPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();

  // Inputs
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>("");
  const [initialCapital, setInitialCapital] = useState<number>(10000);
  const [monthlyContribution, setMonthlyContribution] = useState<number>(500);
  const [durationYears, setDurationYears] = useState<number>(20);
  const [annualReturnPct, setAnnualReturnPct] = useState<number>(7.0);
  const [annualInflationPct, setAnnualInflationPct] = useState<number>(2.5);
  const [annualFeePct, setAnnualFeePct] = useState<number>(0.25);
  const [annualWithdrawal, setAnnualWithdrawal] = useState<number>(0);

  // States
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentRun, setCurrentRun] = useState<SimulationRun | null>(null);
  const [recentRuns, setRecentRuns] = useState<SimulationRun[]>([]);
  const [activeTab, setActiveTab] = useState<"base" | "bear" | "bull">("base");
  const [hoveredYear, setHoveredYear] = useState<number | null>(null);

  // Authentication check
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  // Load portfolios and recent simulations
  useEffect(() => {
    if (!user) return;
    async function loadInitialData() {
      try {
        const [ports, runs] = await Promise.all([
          listPortfolios().catch(() => []),
          listSimulations().catch(() => []),
        ]);
        setPortfolios(ports);
        setRecentRuns(runs);
        if (runs.length > 0) {
          setCurrentRun(runs[0]);
        }
      } catch (err: any) {
        console.error("Failed to load initial simulation data:", err);
      }
    }
    loadInitialData();
  }, [user]);

  // Handle portfolio selection for seeding
  const handlePortfolioSelect = async (portId: string) => {
    setSelectedPortfolioId(portId);
    if (!portId) return;

    try {
      const analytics = await getPortfolioAnalytics(portId);
      const totalVal = parseFloat(analytics.total_value);
      if (!isNaN(totalVal) && totalVal > 0) {
        setInitialCapital(Math.round(totalVal * 100) / 100);
      }
    } catch (err) {
      console.error("Failed to fetch portfolio analytics for seeding:", err);
    }
  };

  // Run simulation
  const handleRunSimulation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsSimulating(true);
    setErrorMessage(null);

    const payload: SimulationRequest = {
      portfolio_id: selectedPortfolioId || null,
      initial_capital: Number(initialCapital),
      monthly_contribution: Number(monthlyContribution),
      duration_years: Number(durationYears),
      annual_return_pct: Number(annualReturnPct),
      annual_inflation_pct: Number(annualInflationPct),
      annual_fee_pct: Number(annualFeePct),
      annual_withdrawal: Number(annualWithdrawal),
    };

    try {
      const run = await createSimulation(payload);
      setCurrentRun(run);
      setRecentRuns((prev) => [run, ...prev.filter((r) => r.id !== run.id)]);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to execute simulation.");
    } finally {
      setIsSimulating(false);
    }
  };

  const handleResetDefaults = () => {
    setSelectedPortfolioId("");
    setInitialCapital(10000);
    setMonthlyContribution(500);
    setDurationYears(20);
    setAnnualReturnPct(7.0);
    setAnnualInflationPct(2.5);
    setAnnualFeePct(0.25);
    setAnnualWithdrawal(0);
    setErrorMessage(null);
  };

  // Format currency
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(val);
  };

  // Auto-run baseline on first load if no current run exists
  useEffect(() => {
    if (user && !currentRun && !isSimulating && recentRuns.length === 0) {
      handleRunSimulation();
    }
  }, [user, currentRun, recentRuns.length]);

  const scenarios = currentRun?.result_json?.scenarios;
  const activeScenario = scenarios ? scenarios[activeTab] : null;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 selection:bg-blue-600 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              href="/app/dashboard"
              className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-400 hover:text-white transition"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Dashboard</span>
            </Link>
            <span className="text-slate-700">|</span>
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Sliders className="h-4 w-4 text-white" />
              </div>
              <span className="text-base font-bold text-white tracking-tight">
                Financial Simulation &amp; Projections
              </span>
            </div>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Deterministic Engine v1
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-400 flex items-center space-x-1.5 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded-full">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              <span>Reproducible Run Engine</span>
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Mandatory Regulatory & Model Disclaimer Banner (§20, §28, §32) */}
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 flex items-start space-x-3.5 shadow-sm">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200/90 leading-relaxed space-y-1">
            <p className="font-semibold text-amber-300">
              Deterministic Multi-Scenario Model Disclosure (§20, §32)
            </p>
            <p>
              These forward projections are mathematical illustrations based on user-supplied assumptions, fixed compound growth, fee drag, and inflation adjustments. <strong>They do not constitute financial advice, predictive guarantees, or statistical probability distributions.</strong> Real market returns fluctuate, involve risk of loss, and vary non-linearly over time.
            </p>
          </div>
        </div>

        {/* Layout Grid: Controls on Left, Visualizer & Results on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Controls Card */}
          <div className="lg:col-span-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center space-x-2">
                <Sliders className="h-4 w-4 text-blue-400" />
                <h2 className="text-sm font-bold text-white tracking-wide uppercase">Simulation Parameters</h2>
              </div>
              <button
                onClick={handleResetDefaults}
                className="text-slate-400 hover:text-white text-xs flex items-center space-x-1 transition"
                title="Reset to default parameters"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset</span>
              </button>
            </div>

            <form onSubmit={handleRunSimulation} className="space-y-4">
              {/* Optional Portfolio Seeding Dropdown */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                  <span>Seed from Portfolio (Optional)</span>
                  <Briefcase className="h-3 w-3 text-slate-500" />
                </label>
                <select
                  value={selectedPortfolioId}
                  onChange={(e) => handlePortfolioSelect(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition"
                >
                  <option value="">-- Manual Entry (No Portfolio Seed) --</option>
                  {portfolios.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.base_currency})
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-[11px] text-slate-500">
                  Selecting a portfolio automatically seeds initial capital from its current market valuation.
                </p>
              </div>

              {/* Initial Capital */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                  <span>Initial Capital ($)</span>
                  <DollarSign className="h-3 w-3 text-slate-500" />
                </label>
                <input
                  type="number"
                  min="0"
                  step="100"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Math.max(0, Number(e.target.value)))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-blue-500 transition"
                  required
                />
              </div>

              {/* Monthly Contribution */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                  <span>Monthly Contribution ($)</span>
                  <DollarSign className="h-3 w-3 text-slate-500" />
                </label>
                <input
                  type="number"
                  min="0"
                  step="50"
                  value={monthlyContribution}
                  onChange={(e) => setMonthlyContribution(Math.max(0, Number(e.target.value)))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-blue-500 transition"
                  required
                />
              </div>

              {/* Duration in Years */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Investment Horizon (Years): <span className="text-blue-400 font-mono font-bold">{durationYears} yrs</span>
                  </label>
                  <Calendar className="h-3 w-3 text-slate-500" />
                </div>
                <input
                  type="range"
                  min="1"
                  max="40"
                  step="1"
                  value={durationYears}
                  onChange={(e) => setDurationYears(Number(e.target.value))}
                  className="w-full accent-blue-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              {/* Base Expected Annual Return */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Base Annual Return (%): <span className="text-emerald-400 font-mono font-bold">{annualReturnPct}%</span>
                  </label>
                  <Percent className="h-3 w-3 text-slate-500" />
                </div>
                <input
                  type="range"
                  min="1"
                  max="20"
                  step="0.25"
                  value={annualReturnPct}
                  onChange={(e) => setAnnualReturnPct(Number(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              {/* Annual Inflation */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Expected Inflation (%): <span className="text-amber-400 font-mono font-bold">{annualInflationPct}%</span>
                  </label>
                  <Percent className="h-3 w-3 text-slate-500" />
                </div>
                <input
                  type="range"
                  min="0"
                  max="10"
                  step="0.25"
                  value={annualInflationPct}
                  onChange={(e) => setAnnualInflationPct(Number(e.target.value))}
                  className="w-full accent-amber-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              {/* Annual Fee Drag */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Expense / Management Fee (%): <span className="text-red-400 font-mono font-bold">{annualFeePct}%</span>
                  </label>
                  <Percent className="h-3 w-3 text-slate-500" />
                </div>
                <input
                  type="range"
                  min="0"
                  max="3"
                  step="0.05"
                  value={annualFeePct}
                  onChange={(e) => setAnnualFeePct(Number(e.target.value))}
                  className="w-full accent-red-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              {/* Optional Annual Decumulation / Withdrawal */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                  <span>Annual Withdrawal / Decumulation ($)</span>
                  <DollarSign className="h-3 w-3 text-slate-500" />
                </label>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  value={annualWithdrawal}
                  onChange={(e) => setAnnualWithdrawal(Math.max(0, Number(e.target.value)))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-blue-500 transition"
                />
                <p className="mt-1 text-[11px] text-slate-500">
                  Optional yearly withdrawal deducted during the projection horizon.
                </p>
              </div>

              {errorMessage && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  {errorMessage}
                </div>
              )}

              <button
                type="submit"
                disabled={isSimulating}
                className="w-full mt-2 inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs tracking-wide shadow-lg shadow-blue-500/20 disabled:opacity-50 transition"
              >
                {isSimulating ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Computing Trajectories...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Run Multi-Scenario Simulation</span>
                  </>
                )}
              </button>
            </form>

            {/* Run History Quick Select */}
            {recentRuns.length > 1 && (
              <div className="pt-4 border-t border-slate-800/80">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-400 mb-2">
                  <History className="h-3.5 w-3.5" />
                  <span>Recent Saved Runs</span>
                </div>
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {recentRuns.slice(0, 5).map((r) => (
                    <button
                      key={r.id}
                      onClick={() => setCurrentRun(r)}
                      className={`w-full text-left px-2.5 py-1.5 rounded-lg text-[11px] flex items-center justify-between border transition ${
                        currentRun?.id === r.id
                          ? "bg-blue-600/10 border-blue-500/30 text-blue-300"
                          : "bg-slate-950/40 border-slate-800/60 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <span className="font-mono">
                        ${r.input_json.initial_capital} &bull; {r.input_json.duration_years}y @ {r.input_json.annual_return_pct}%
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {new Date(r.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Visualization & Milestones */}
          <div className="lg:col-span-8 space-y-6">
            {scenarios ? (
              <>
                {/* Visualizer Chart Card */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800/80 pb-4">
                    <div>
                      <h3 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
                        <span>Projected Trajectories</span>
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          Deterministic Multi-Scenario
                        </span>
                      </h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Fixed compound interest curves &bull; 3 distinct deterministic trajectories (not a distribution)
                      </p>
                    </div>

                    {/* Chart Legend */}
                    <div className="flex items-center space-x-4 text-xs">
                      <div className="flex items-center space-x-1.5">
                        <div className="w-3 h-1 bg-rose-500 rounded-full" />
                        <span className="text-slate-300 font-medium">Bear</span>
                        <span className="text-slate-500 text-[10px]">
                          ({scenarios.bear.assumptions.annual_return_pct}%)
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <div className="w-3 h-1 bg-emerald-400 rounded-full" />
                        <span className="text-slate-300 font-medium">Base</span>
                        <span className="text-slate-500 text-[10px]">
                          ({scenarios.base.assumptions.annual_return_pct}%)
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <div className="w-3 h-1 bg-indigo-400 rounded-full" />
                        <span className="text-slate-300 font-medium">Bull</span>
                        <span className="text-slate-500 text-[10px]">
                          ({scenarios.bull.assumptions.annual_return_pct}%)
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* SVG Multi-Scenario Line Chart (Honest: 3 distinct strokes, NO shaded fans) */}
                  <div className="relative w-full h-72 pt-2">
                    <SimulationChart
                      scenarios={scenarios}
                      durationYears={currentRun.input_json.duration_years}
                      hoveredYear={hoveredYear}
                      setHoveredYear={setHoveredYear}
                      formatCurrency={formatCurrency}
                    />
                  </div>

                  {/* Clarification Callout below chart */}
                  <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-3">
                    <div className="flex items-center space-x-1.5">
                      <Info className="h-3.5 w-3.5 text-blue-400" />
                      <span>Solid lines illustrate mathematical compounding of fixed annual returns after fees.</span>
                    </div>
                    <span className="font-mono text-[10px] text-slate-500">
                      Engine: {currentRun.engine_version}
                    </span>
                  </div>
                </div>

                {/* Scenario Comparison KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Bear Scenario Card */}
                  <div
                    onClick={() => setActiveTab("bear")}
                    className={`cursor-pointer rounded-xl p-4 border transition ${
                      activeTab === "bear"
                        ? "bg-rose-500/10 border-rose-500/40 shadow-lg shadow-rose-500/5 ring-1 ring-rose-500/30"
                        : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-rose-400">Bear Scenario</span>
                      <span className="text-[10px] text-slate-400 font-mono">{scenarios.bear.assumptions.annual_return_pct}% return</span>
                    </div>
                    <div className="mt-2">
                      <div className="text-xl font-extrabold text-white font-mono">
                        {formatCurrency(scenarios.bear.result.nominal_ending_value)}
                      </div>
                      <div className="text-xs text-slate-400 mt-1 flex items-center space-x-1">
                        <span>Real (Purchasing Power):</span>
                        <strong className="text-rose-300 font-mono">
                          {formatCurrency(scenarios.bear.result.real_ending_value)}
                        </strong>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Total Invested</span>
                      <span className="font-mono font-medium text-slate-300">
                        {formatCurrency(scenarios.bear.result.total_contributions)}
                      </span>
                    </div>
                  </div>

                  {/* Base Scenario Card */}
                  <div
                    onClick={() => setActiveTab("base")}
                    className={`cursor-pointer rounded-xl p-4 border transition ${
                      activeTab === "base"
                        ? "bg-emerald-500/10 border-emerald-500/40 shadow-lg shadow-emerald-500/5 ring-1 ring-emerald-500/30"
                        : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Base Scenario</span>
                      <span className="text-[10px] text-slate-400 font-mono">{scenarios.base.assumptions.annual_return_pct}% return</span>
                    </div>
                    <div className="mt-2">
                      <div className="text-xl font-extrabold text-white font-mono">
                        {formatCurrency(scenarios.base.result.nominal_ending_value)}
                      </div>
                      <div className="text-xs text-slate-400 mt-1 flex items-center space-x-1">
                        <span>Real (Purchasing Power):</span>
                        <strong className="text-emerald-300 font-mono">
                          {formatCurrency(scenarios.base.result.real_ending_value)}
                        </strong>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Total Invested</span>
                      <span className="font-mono font-medium text-slate-300">
                        {formatCurrency(scenarios.base.result.total_contributions)}
                      </span>
                    </div>
                  </div>

                  {/* Bull Scenario Card */}
                  <div
                    onClick={() => setActiveTab("bull")}
                    className={`cursor-pointer rounded-xl p-4 border transition ${
                      activeTab === "bull"
                        ? "bg-indigo-500/10 border-indigo-500/40 shadow-lg shadow-indigo-500/5 ring-1 ring-indigo-500/30"
                        : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Bull Scenario</span>
                      <span className="text-[10px] text-slate-400 font-mono">{scenarios.bull.assumptions.annual_return_pct}% return</span>
                    </div>
                    <div className="mt-2">
                      <div className="text-xl font-extrabold text-white font-mono">
                        {formatCurrency(scenarios.bull.result.nominal_ending_value)}
                      </div>
                      <div className="text-xs text-slate-400 mt-1 flex items-center space-x-1">
                        <span>Real (Purchasing Power):</span>
                        <strong className="text-indigo-300 font-mono">
                          {formatCurrency(scenarios.bull.result.real_ending_value)}
                        </strong>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Total Invested</span>
                      <span className="font-mono font-medium text-slate-300">
                        {formatCurrency(scenarios.bull.result.total_contributions)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Scenario Milestones Table */}
                {activeScenario && (
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800/80 pb-3">
                      <div className="flex items-center space-x-2">
                        <FileSpreadsheet className="h-4 w-4 text-cyan-400" />
                        <h4 className="text-sm font-bold text-white">
                          Yearly Schedule &bull; {activeScenario.label}
                        </h4>
                      </div>

                      {/* Tab Switcher */}
                      <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800">
                        <button
                          onClick={() => setActiveTab("bear")}
                          className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                            activeTab === "bear"
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          Bear
                        </button>
                        <button
                          onClick={() => setActiveTab("base")}
                          className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                            activeTab === "base"
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          Base
                        </button>
                        <button
                          onClick={() => setActiveTab("bull")}
                          className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                            activeTab === "bull"
                              ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          Bull
                        </button>
                      </div>
                    </div>

                    {/* Table */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                            <th className="py-2.5 px-3">Year</th>
                            <th className="py-2.5 px-3 text-right">Start Balance</th>
                            <th className="py-2.5 px-3 text-right">Contributions</th>
                            <th className="py-2.5 px-3 text-right">Withdrawals</th>
                            <th className="py-2.5 px-3 text-right">Growth</th>
                            <th className="py-2.5 px-3 text-right">Fees Drag</th>
                            <th className="py-2.5 px-3 text-right">Nominal Balance</th>
                            <th className="py-2.5 px-3 text-right text-cyan-300">Real Balance</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50 font-mono text-[11px]">
                          {activeScenario.result.yearly_snapshots.map((snap) => (
                            <tr
                              key={snap.year}
                              className={`hover:bg-slate-800/30 transition ${
                                hoveredYear === snap.year ? "bg-blue-600/10" : ""
                              }`}
                            >
                              <td className="py-2.5 px-3 font-sans font-medium text-slate-300">
                                Year {snap.year}
                              </td>
                              <td className="py-2.5 px-3 text-right text-slate-400">
                                {formatCurrency(snap.starting_balance)}
                              </td>
                              <td className="py-2.5 px-3 text-right text-emerald-400">
                                +{formatCurrency(snap.contributions)}
                              </td>
                              <td className="py-2.5 px-3 text-right text-amber-400">
                                {snap.withdrawals > 0 ? `-${formatCurrency(snap.withdrawals)}` : "$0"}
                              </td>
                              <td className="py-2.5 px-3 text-right text-blue-400">
                                +{formatCurrency(snap.investment_growth)}
                              </td>
                              <td className="py-2.5 px-3 text-right text-rose-400">
                                -{formatCurrency(snap.fees_paid)}
                              </td>
                              <td className="py-2.5 px-3 text-right font-bold text-white">
                                {formatCurrency(snap.ending_nominal_value)}
                              </td>
                              <td className="py-2.5 px-3 text-right font-bold text-cyan-300">
                                {formatCurrency(snap.ending_real_value)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-3">
                <Sliders className="h-8 w-8 text-slate-600 animate-pulse" />
                <h4 className="text-base font-semibold text-slate-300">Ready to simulate</h4>
                <p className="text-xs text-slate-500 max-w-sm">
                  Adjust parameters on the left and click &ldquo;Run Multi-Scenario Simulation&rdquo; to compute deterministic projections.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SVG Multi-Scenario Line Chart (Strictly honest, 3 trajectories, no shading)
// ---------------------------------------------------------------------------
interface SimulationChartProps {
  scenarios: SimulationResultJson["scenarios"];
  durationYears: number;
  hoveredYear: number | null;
  setHoveredYear: (yr: number | null) => void;
  formatCurrency: (val: number) => string;
}

function SimulationChart({
  scenarios,
  durationYears,
  hoveredYear,
  setHoveredYear,
  formatCurrency,
}: SimulationChartProps) {
  const chartId = useId();
  const bearSnaps = scenarios.bear.result.yearly_snapshots;
  const baseSnaps = scenarios.base.result.yearly_snapshots;
  const bullSnaps = scenarios.bull.result.yearly_snapshots;

  const width = 760;
  const height = 260;
  const padding = { top: 20, right: 30, bottom: 35, left: 75 };

  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  // Max value across all scenarios for scaling
  const maxVal = Math.max(
    ...bullSnaps.map((s) => Number(s.ending_nominal_value) || 0),
    ...baseSnaps.map((s) => Number(s.ending_nominal_value) || 0),
    ...bearSnaps.map((s) => Number(s.ending_nominal_value) || 0),
    1000
  );

  const getX = (year: number) => {
    return padding.left + ((year - 1) / Math.max(1, durationYears - 1)) * innerWidth;
  };

  const getY = (val: number) => {
    return padding.top + innerHeight - (val / maxVal) * innerHeight;
  };

  // Generate SVG path strings
  const generatePath = (snaps: typeof baseSnaps) => {
    return snaps
      .map((s, idx) => {
        const x = getX(s.year);
        const y = getY(Number(s.ending_nominal_value) || 0);
        return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  };

  const bearPath = generatePath(bearSnaps);
  const basePath = generatePath(baseSnaps);
  const bullPath = generatePath(bullSnaps);

  // Y-axis ticks
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((pct) => ({
    val: maxVal * pct,
    y: padding.top + innerHeight - pct * innerHeight,
  }));

  // X-axis ticks (e.g. 5 ticks)
  const step = Math.max(1, Math.floor(durationYears / 5));
  const xTicks: number[] = [];
  for (let yr = 1; yr <= durationYears; yr += step) {
    xTicks.push(yr);
  }
  if (!xTicks.includes(durationYears)) {
    xTicks.push(durationYears);
  }

  // Active hover data
  const hoverBear = hoveredYear ? bearSnaps.find((s) => s.year === hoveredYear) : null;
  const hoverBase = hoveredYear ? baseSnaps.find((s) => s.year === hoveredYear) : null;
  const hoverBull = hoveredYear ? bullSnaps.find((s) => s.year === hoveredYear) : null;

  return (
    <div className="relative w-full h-full select-none">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full overflow-visible"
        onMouseLeave={() => setHoveredYear(null)}
      >
        <defs>
          <filter id={`glow-${chartId}`} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Horizontal grid lines */}
        {yTicks.map((tick, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              y1={tick.y}
              x2={width - padding.right}
              y2={tick.y}
              stroke="#1e293b"
              strokeDasharray="3 3"
              strokeWidth="1"
            />
            <text
              x={padding.left - 8}
              y={tick.y + 3}
              textAnchor="end"
              className="text-[10px] fill-slate-500 font-mono"
            >
              {formatCurrency(tick.val)}
            </text>
          </g>
        ))}

        {/* Vertical year ticks */}
        {xTicks.map((yr) => (
          <g key={yr}>
            <line
              x1={getX(yr)}
              y1={padding.top}
              x2={getX(yr)}
              y2={height - padding.bottom}
              stroke="#1e293b"
              strokeDasharray="2 4"
              strokeWidth="1"
            />
            <text
              x={getX(yr)}
              y={height - padding.bottom + 16}
              textAnchor="middle"
              className="text-[10px] fill-slate-500 font-mono"
            >
              Yr {yr}
            </text>
          </g>
        ))}

        {/* 3 Honest Trajectory Lines (No fill / shading) */}
        {/* Bear: Rose */}
        <path
          d={bearPath}
          fill="none"
          stroke="#f43f5e"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all"
        />

        {/* Base: Emerald */}
        <path
          d={basePath}
          fill="none"
          stroke="#10b981"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all"
        />

        {/* Bull: Indigo */}
        <path
          d={bullPath}
          fill="none"
          stroke="#818cf8"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all"
        />

        {/* Interactive hover scrub columns */}
        {baseSnaps.map((s) => {
          const colX = getX(s.year);
          const colW = innerWidth / Math.max(1, durationYears);
          return (
            <rect
              key={s.year}
              x={colX - colW / 2}
              y={padding.top}
              width={colW}
              height={innerHeight}
              fill="transparent"
              className="cursor-pointer"
              onMouseEnter={() => setHoveredYear(s.year)}
            />
          );
        })}

        {/* Hover vertical line and circles */}
        {hoveredYear && (
          <g>
            <line
              x1={getX(hoveredYear)}
              y1={padding.top}
              x2={getX(hoveredYear)}
              y2={height - padding.bottom}
              stroke="#38bdf8"
              strokeWidth="1.5"
              strokeDasharray="2 2"
            />
            {hoverBear && (
              <circle
                cx={getX(hoveredYear)}
                cy={getY(Number(hoverBear.ending_nominal_value) || 0)}
                r="4.5"
                fill="#f43f5e"
                stroke="#090d16"
                strokeWidth="2"
              />
            )}
            {hoverBase && (
              <circle
                cx={getX(hoveredYear)}
                cy={getY(Number(hoverBase.ending_nominal_value) || 0)}
                r="5"
                fill="#10b981"
                stroke="#090d16"
                strokeWidth="2"
              />
            )}
            {hoverBull && (
              <circle
                cx={getX(hoveredYear)}
                cy={getY(Number(hoverBull.ending_nominal_value) || 0)}
                r="4.5"
                fill="#818cf8"
                stroke="#090d16"
                strokeWidth="2"
              />
            )}
          </g>
        )}
      </svg>

      {/* Floating Hover Tooltip */}
      {hoveredYear && hoverBase && hoverBear && hoverBull && (
        <div
          className="absolute z-20 pointer-events-none bg-slate-950/95 border border-slate-700/80 rounded-xl p-3 shadow-2xl text-xs backdrop-blur-md"
          style={{
            left: Math.min(Math.max(getX(hoveredYear) - 70, 10), width - 180),
            top: 10,
          }}
        >
          <div className="font-bold text-slate-200 border-b border-slate-800 pb-1.5 mb-1.5 flex items-center justify-between">
            <span>Year {hoveredYear} Trajectory</span>
            <span className="text-[10px] text-slate-500 font-normal">Deterministic</span>
          </div>
          <div className="space-y-1 font-mono text-[11px]">
            <div className="flex items-center justify-between space-x-3 text-indigo-300">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-indigo-400 inline-block" />
                <span>Bull:</span>
              </span>
              <span className="font-bold">{formatCurrency(hoverBull.ending_nominal_value)}</span>
            </div>
            <div className="flex items-center justify-between space-x-3 text-emerald-300">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                <span>Base:</span>
              </span>
              <span className="font-bold">{formatCurrency(hoverBase.ending_nominal_value)}</span>
            </div>
            <div className="flex items-center justify-between space-x-3 text-rose-300">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-rose-400 inline-block" />
                <span>Bear:</span>
              </span>
              <span className="font-bold">{formatCurrency(hoverBear.ending_nominal_value)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
