"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  Briefcase,
  Plus,
  ArrowRight,
  ArrowLeft,
  DollarSign,
  PieChart,
  BarChart3,
  Layers,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Trash2,
  RefreshCw,
  Loader2,
  Sparkles,
  Percent,
  Clock,
  ChevronRight,
  Sliders,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";
import {
  Portfolio,
  Holding,
  Transaction,
  PortfolioAnalytics,
  listPortfolios,
  createPortfolio,
  listHoldings,
  createHolding,
  deleteHolding,
  recordTransaction,
  getPortfolioAnalytics,
} from "@/lib/portfolio";

export default function PortfolioPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();

  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [analytics, setAnalytics] = useState<PortfolioAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showAddHoldingModal, setShowAddHoldingModal] = useState<boolean>(false);
  const [showAddTxModal, setShowAddTxModal] = useState<boolean>(false);

  // Form states
  const [newPortfolioName, setNewPortfolioName] = useState("");
  const [isVirtual, setIsVirtual] = useState(true);

  // Holding form
  const [holdingSymbol, setHoldingSymbol] = useState("AAPL");
  const [holdingQty, setHoldingQty] = useState("10");
  const [holdingCost, setHoldingCost] = useState("200");
  const [holdingPrice, setHoldingPrice] = useState("225");
  const [holdingSector, setHoldingSector] = useState("Technology");

  // Transaction form
  const [txSymbol, setTxSymbol] = useState("MSFT");
  const [txType, setTxType] = useState<"buy" | "sell">("buy");
  const [txQty, setTxQty] = useState("5");
  const [txPrice, setTxPrice] = useState("410");

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
      return;
    }

    if (user) {
      loadInitialData();
    }
  }, [user, isAuthLoading, router]);

  async function loadInitialData() {
    setIsLoading(true);
    setError(null);
    try {
      const pList = await listPortfolios();
      setPortfolios(pList);
      if (pList.length > 0) {
        setSelectedPortfolio(pList[0]);
        await loadPortfolioDetails(pList[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load portfolios");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadPortfolioDetails(portfolioId: string) {
    setIsRefreshing(true);
    try {
      const [hList, aData] = await Promise.all([
        listHoldings(portfolioId),
        getPortfolioAnalytics(portfolioId),
      ]);
      setHoldings(hList);
      setAnalytics(aData);
    } catch (err: any) {
      setError(err.message || "Failed to load portfolio details");
    } finally {
      setIsRefreshing(false);
    }
  }

  const handleSelectPortfolio = async (p: Portfolio) => {
    setSelectedPortfolio(p);
    await loadPortfolioDetails(p.id);
  };

  const handleCreatePortfolio = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPortfolioName.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const created = await createPortfolio({
        name: newPortfolioName.trim(),
        portfolio_type: isVirtual ? "virtual" : "manual",
        is_virtual: isVirtual,
      });
      setPortfolios((prev) => [created, ...prev]);
      setSelectedPortfolio(created);
      setShowCreateModal(false);
      setNewPortfolioName("");
      await loadPortfolioDetails(created.id);
    } catch (err: any) {
      setError(err.message || "Failed to create portfolio");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolio) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await createHolding(selectedPortfolio.id, {
        symbol: holdingSymbol.trim().toUpperCase(),
        quantity: parseFloat(holdingQty) || 1,
        average_cost: parseFloat(holdingCost) || 0,
        current_price: parseFloat(holdingPrice) || undefined,
        sector: holdingSector,
      });
      setShowAddHoldingModal(false);
      await loadPortfolioDetails(selectedPortfolio.id);
    } catch (err: any) {
      setError(err.message || "Failed to add holding");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteHolding = async (holdingId: string) => {
    if (!selectedPortfolio) return;
    try {
      await deleteHolding(selectedPortfolio.id, holdingId);
      await loadPortfolioDetails(selectedPortfolio.id);
    } catch (err: any) {
      setError(err.message || "Failed to delete holding");
    }
  };

  const handleRecordTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolio) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const idempotencyKey = `tx-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      await recordTransaction(selectedPortfolio.id, {
        symbol: txSymbol.trim().toUpperCase(),
        transaction_type: txType,
        quantity: parseFloat(txQty) || 1,
        price: parseFloat(txPrice) || 0,
        idempotency_key: idempotencyKey,
      });
      setShowAddTxModal(false);
      await loadPortfolioDetails(selectedPortfolio.id);
    } catch (err: any) {
      setError(err.message || "Failed to record transaction");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Instant starter kit to load a virtual diversified portfolio for instant analytics verification
  const handleLoadVirtualStarterKit = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const created = await createPortfolio({
        name: "All-Weather Strategic Growth",
        portfolio_type: "virtual",
        is_virtual: true,
      });

      // Populate core diverse assets
      await Promise.all([
        createHolding(created.id, { symbol: "VTI", quantity: 25, average_cost: 260, current_price: 275, sector: "Broad Market" }),
        createHolding(created.id, { symbol: "AAPL", quantity: 15, average_cost: 210, current_price: 225, sector: "Technology" }),
        createHolding(created.id, { symbol: "MSFT", quantity: 10, average_cost: 410, current_price: 430, sector: "Technology" }),
        createHolding(created.id, { symbol: "JNJ", quantity: 15, average_cost: 150, current_price: 160, sector: "Healthcare" }),
        createHolding(created.id, { symbol: "BND", quantity: 40, average_cost: 72, current_price: 73.5, sector: "Fixed Income" }),
      ]);

      setPortfolios((prev) => [created, ...prev]);
      setSelectedPortfolio(created);
      await loadPortfolioDetails(created.id);
    } catch (err: any) {
      setError(err.message || "Failed to instantiate virtual starter portfolio");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isAuthLoading || isLoading) {
    return (
      <div className="min-h-screen bg-[#090d16] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="h-10 w-10 text-emerald-500 animate-spin" />
        <p className="text-sm text-slate-400">Loading portfolio analytics engine...</p>
      </div>
    );
  }

  const totalValue = analytics ? Number(analytics.total_value) : 0;
  const totalCost = analytics ? Number(analytics.total_cost) : 0;
  const gainLoss = analytics ? Number(analytics.unrealized_gain_loss) : 0;
  const gainLossPct = analytics?.unrealized_gain_loss_pct ? Number(analytics.unrealized_gain_loss_pct) * 100 : 0;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col selection:bg-emerald-600 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Link href="/app/dashboard" className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Briefcase className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white">FinSight</span>
            </Link>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Deterministic Financial Engine
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/app/dashboard"
              className="text-xs text-slate-400 hover:text-slate-200 transition flex items-center space-x-1"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Dashboard</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Error notification */}
        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-slate-400 hover:text-white text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Portfolio Selector & Actions Bar */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl border border-slate-800 bg-slate-900/40">
          <div className="flex items-center space-x-3 overflow-x-auto max-w-full pb-2 md:pb-0">
            {portfolios.map((p) => {
              const isSelected = selectedPortfolio?.id === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSelectPortfolio(p)}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold transition shrink-0 flex items-center space-x-2 ${
                    isSelected
                      ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/20"
                      : "bg-slate-950/60 border border-slate-800 text-slate-300 hover:border-slate-700"
                  }`}
                >
                  <span>{p.name}</span>
                  {p.is_virtual && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
                      Virtual
                    </span>
                  )}
                </button>
              );
            })}

            <button
              onClick={() => setShowCreateModal(true)}
              className="px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-300 hover:text-white transition flex items-center space-x-1.5 shrink-0"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Portfolio</span>
            </button>
          </div>

          <div className="flex items-center space-x-3 w-full md:w-auto justify-end">
            {portfolios.length === 0 && (
              <button
                onClick={handleLoadVirtualStarterKit}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold transition flex items-center space-x-2 shadow-lg shadow-emerald-500/20"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Instantiate Demo Strategy</span>
              </button>
            )}

            {selectedPortfolio && (
              <>
                <button
                  onClick={() => setShowAddHoldingModal(true)}
                  className="px-3.5 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-300 text-xs font-medium transition flex items-center space-x-1.5"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Add Holding</span>
                </button>

                <button
                  onClick={() => setShowAddTxModal(true)}
                  className="px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition flex items-center space-x-1.5"
                >
                  <Sliders className="h-3.5 w-3.5" />
                  <span>Log Transaction</span>
                </button>

                <button
                  onClick={() => selectedPortfolio && loadPortfolioDetails(selectedPortfolio.id)}
                  disabled={isRefreshing}
                  className="p-2 rounded-xl border border-slate-800 bg-slate-900/60 text-slate-400 hover:text-white transition"
                  title="Refresh valuation"
                >
                  <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin text-emerald-400" : ""}`} />
                </button>
              </>
            )}
          </div>
        </div>

        {/* If no portfolios exist */}
        {portfolios.length === 0 ? (
          <div className="p-16 rounded-3xl border border-slate-800 bg-slate-900/30 text-center max-w-xl mx-auto space-y-5">
            <div className="h-16 w-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
              <Briefcase className="h-8 w-8" />
            </div>
            <h2 className="text-xl font-bold text-white">No Portfolios Found</h2>
            <p className="text-slate-400 text-xs leading-relaxed">
              Create a virtual sandbox portfolio to test asset allocations, calculate deterministic CAGR &amp; XIRR returns, and inspect concentration risk without risking real capital.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setShowCreateModal(true)}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
              >
                Create Virtual Portfolio
              </button>
              <button
                onClick={handleLoadVirtualStarterKit}
                disabled={isSubmitting}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-slate-700 hover:border-slate-600 bg-slate-800/60 text-slate-200 text-xs font-semibold transition flex items-center justify-center space-x-2"
              >
                <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                <span>Load Balanced Starter Kit</span>
              </button>
            </div>
          </div>
        ) : (
          /* Active Portfolio Dashboard */
          <div className="space-y-8 animate-in fade-in-50 duration-300">
            {/* KPI Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total Value */}
              <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50 relative overflow-hidden">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                  <span>Total Valuation</span>
                  <DollarSign className="h-4 w-4 text-emerald-400" />
                </div>
                <div className="mt-2 text-2xl font-black text-white tracking-tight">
                  ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="mt-1 text-[11px] text-slate-500">
                  Across {holdings.length} tracked asset{holdings.length === 1 ? "" : "s"}
                </div>
              </div>

              {/* Total Cost Basis */}
              <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                  <span>Cost Basis / Capital</span>
                  <Layers className="h-4 w-4 text-slate-400" />
                </div>
                <div className="mt-2 text-2xl font-black text-slate-200 tracking-tight">
                  ${totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="mt-1 text-[11px] text-slate-500">
                  Net cumulative invested capital
                </div>
              </div>

              {/* Total Return */}
              <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                  <span>Unrealized Return</span>
                  <Percent className={`h-4 w-4 ${gainLoss >= 0 ? "text-emerald-400" : "text-rose-400"}`} />
                </div>
                <div className={`mt-2 text-2xl font-black tracking-tight ${gainLoss >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {gainLoss >= 0 ? "+" : ""}${gainLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="mt-1 text-[11px] flex items-center space-x-1 font-semibold">
                  <span className={gainLoss >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    {gainLoss >= 0 ? "+" : ""}{gainLossPct.toFixed(2)}%
                  </span>
                  <span className="text-slate-500 font-normal">all-time yield</span>
                </div>
              </div>

              {/* Concentration / XIRR */}
              <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                  <span>Concentration Risk</span>
                  <ShieldCheck className="h-4 w-4 text-blue-400" />
                </div>
                <div className="mt-2 text-2xl font-black text-white tracking-tight capitalize">
                  {analytics?.concentration.concentration_level.replace(/_/g, " ") || "Diversified"}
                </div>
                <div className="mt-1 text-[11px] text-slate-400 flex items-center space-x-2">
                  <span>HHI: {analytics ? Math.round(Number(analytics.concentration.hhi)) : 0}</span>
                  <span>•</span>
                  <span>Top: {analytics ? (Number(analytics.concentration.top_1_weight) * 100).toFixed(1) : 0}%</span>
                </div>
              </div>
            </div>

            {/* Asset Allocation & Sector Exposures Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Asset Allocation Breakdown */}
              <div className="p-6 rounded-3xl border border-slate-800 bg-slate-900/40 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <PieChart className="h-4 w-4 text-emerald-400" />
                    <h3 className="text-sm font-bold text-white">Asset Allocation Weights</h3>
                  </div>
                  <span className="text-xs text-slate-400">Sum: 100%</span>
                </div>

                {analytics && analytics.allocations.length > 0 ? (
                  <div className="space-y-3 pt-2">
                    {analytics.allocations.map((a, idx) => {
                      const pct = Number(a.weight_pct);
                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-slate-200">
                              {a.symbol} <span className="font-normal text-slate-400 text-[11px]">({a.name})</span>
                            </span>
                            <span className="font-mono text-emerald-400 font-semibold">{pct.toFixed(1)}%</span>
                          </div>
                          <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 py-6 text-center">Add holdings to view asset allocations.</p>
                )}
              </div>

              {/* Sector Exposures */}
              <div className="p-6 rounded-3xl border border-slate-800 bg-slate-900/40 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="h-4 w-4 text-blue-400" />
                    <h3 className="text-sm font-bold text-white">Sector Exposure Distribution</h3>
                  </div>
                  <span className="text-xs text-slate-400">{analytics?.sector_exposures.length || 0} Sectors</span>
                </div>

                {analytics && analytics.sector_exposures.length > 0 ? (
                  <div className="space-y-3 pt-2">
                    {analytics.sector_exposures.map((s, idx) => {
                      const pct = Number(s.weight_pct);
                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-medium text-slate-300">{s.sector}</span>
                            <span className="font-mono text-blue-400 font-semibold">{pct.toFixed(1)}%</span>
                          </div>
                          <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-indigo-400 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 py-6 text-center">No sector exposures calculated yet.</p>
                )}
              </div>
            </div>

            {/* Holdings Table */}
            <div className="rounded-3xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-slate-800/80 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white">Portfolio Holdings</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Deterministic valuations computed directly via pure Python Decimal Financial Engine (§19).
                  </p>
                </div>
                <button
                  onClick={() => setShowAddHoldingModal(true)}
                  className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition flex items-center space-x-1"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Add Position</span>
                </button>
              </div>

              {holdings.length === 0 ? (
                <div className="p-12 text-center text-xs text-slate-500">
                  No positions added yet. Click &quot;Add Position&quot; to record your first holding.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-800">
                      <tr>
                        <th className="py-3.5 px-6">Asset</th>
                        <th className="py-3.5 px-4">Class / Sector</th>
                        <th className="py-3.5 px-4 text-right">Shares</th>
                        <th className="py-3.5 px-4 text-right">Avg Cost</th>
                        <th className="py-3.5 px-4 text-right">Price</th>
                        <th className="py-3.5 px-4 text-right">Market Value</th>
                        <th className="py-3.5 px-4 text-right">Unrealized P&amp;L</th>
                        <th className="py-3.5 px-6 text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-200">
                      {holdings.map((h) => {
                        const val = h.current_value ? Number(h.current_value) : 0;
                        const gain = h.unrealized_gain_loss ? Number(h.unrealized_gain_loss) : 0;
                        const gainPct = h.unrealized_gain_loss_pct ? Number(h.unrealized_gain_loss_pct) * 100 : 0;
                        return (
                          <tr key={h.id} className="hover:bg-slate-800/30 transition">
                            <td className="py-4 px-6 font-bold text-white flex flex-col">
                              <span>{h.symbol}</span>
                              <span className="text-[11px] font-normal text-slate-400">{h.name}</span>
                            </td>
                            <td className="py-4 px-4">
                              <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-300 font-medium">
                                {h.sector || h.asset_type}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-right font-mono font-medium">
                              {Number(h.quantity).toLocaleString()}
                            </td>
                            <td className="py-4 px-4 text-right font-mono text-slate-400">
                              ${Number(h.average_cost).toFixed(2)}
                            </td>
                            <td className="py-4 px-4 text-right font-mono text-white font-medium">
                              ${h.current_price ? Number(h.current_price).toFixed(2) : "---"}
                            </td>
                            <td className="py-4 px-4 text-right font-mono font-bold text-white">
                              ${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </td>
                            <td className="py-4 px-4 text-right font-mono font-semibold">
                              <span className={gain >= 0 ? "text-emerald-400" : "text-rose-400"}>
                                {gain >= 0 ? "+" : ""}${gain.toFixed(2)} ({gain >= 0 ? "+" : ""}{gainPct.toFixed(1)}%)
                              </span>
                            </td>
                            <td className="py-4 px-6 text-center">
                              <button
                                onClick={() => handleDeleteHolding(h.id)}
                                className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                                title="Remove position"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Modal: Create Portfolio */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Create New Portfolio</h3>
            <form onSubmit={handleCreatePortfolio} className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Portfolio Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Core Equity Growth"
                  value={newPortfolioName}
                  onChange={(e) => setNewPortfolioName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center space-x-3 pt-2">
                <input
                  type="checkbox"
                  id="isVirtual"
                  checked={isVirtual}
                  onChange={(e) => setIsVirtual(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-emerald-600 focus:ring-0"
                />
                <label htmlFor="isVirtual" className="text-xs text-slate-300">
                  Virtual Simulation Portfolio (Simulated assets)
                </label>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
                >
                  {isSubmitting ? "Creating..." : "Create Portfolio"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Holding */}
      {showAddHoldingModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Add Position</h3>
            <form onSubmit={handleAddHolding} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Ticker Symbol</label>
                  <input
                    type="text"
                    required
                    placeholder="AAPL, VTI..."
                    value={holdingSymbol}
                    onChange={(e) => setHoldingSymbol(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs uppercase focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Sector (Optional)</label>
                  <input
                    type="text"
                    placeholder="Technology..."
                    value={holdingSector}
                    onChange={(e) => setHoldingSector(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Shares</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={holdingQty}
                    onChange={(e) => setHoldingQty(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Avg Cost ($)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={holdingCost}
                    onChange={(e) => setHoldingCost(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Price ($)</label>
                  <input
                    type="number"
                    step="any"
                    value={holdingPrice}
                    onChange={(e) => setHoldingPrice(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddHoldingModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
                >
                  {isSubmitting ? "Adding..." : "Add Position"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Log Transaction */}
      {showAddTxModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Log Transaction</h3>
            <form onSubmit={handleRecordTransaction} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Ticker</label>
                  <input
                    type="text"
                    required
                    value={txSymbol}
                    onChange={(e) => setTxSymbol(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs uppercase focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Type</label>
                  <select
                    value={txType}
                    onChange={(e) => setTxType(e.target.value as "buy" | "sell")}
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                  >
                    <option value="buy">Buy (Add shares)</option>
                    <option value="sell">Sell (Reduce shares)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Quantity</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={txQty}
                    onChange={(e) => setTxQty(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Price ($)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={txPrice}
                    onChange={(e) => setTxPrice(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddTxModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
                >
                  {isSubmitting ? "Saving..." : "Record Transaction"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
