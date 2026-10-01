"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  User,
  ShieldCheck,
  Brain,
  BarChart3,
  Target,
  Plus,
  Trash2,
  Edit2,
  Save,
  X,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Loader2,
  Calendar,
  DollarSign,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";
import {
  getProfile,
  getLatestAssessment,
  getGoals,
  createGoal,
  deleteGoal,
  updateProfile,
  FinancialProfile,
  ProfileAssessment,
  FinancialGoal,
} from "@/lib/profile";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();

  const [profile, setProfile] = useState<FinancialProfile | null>(null);
  const [assessment, setAssessment] = useState<ProfileAssessment | null>(null);
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // How was this determined toggle
  const [showHowDetermined, setShowHowDetermined] = useState<boolean>(false);

  // Edit capital/contribution modal or inline
  const [isEditingCapital, setIsEditingCapital] = useState<boolean>(false);
  const [editCapital, setEditCapital] = useState<string>("");
  const [editContribution, setEditContribution] = useState<string>("");
  const [isSavingProfile, setIsSavingProfile] = useState<boolean>(false);

  // Add Goal form
  const [showAddGoal, setShowAddGoal] = useState<boolean>(false);
  const [newGoalName, setNewGoalName] = useState<string>("");
  const [newGoalType, setNewGoalType] = useState<string>("retirement");
  const [newGoalAmount, setNewGoalAmount] = useState<string>("");
  const [newGoalDate, setNewGoalDate] = useState<string>("");
  const [isSavingGoal, setIsSavingGoal] = useState<boolean>(false);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
      return;
    }

    async function loadData() {
      try {
        const [prof, assess, userGoals] = await Promise.all([
          getProfile(),
          getLatestAssessment(),
          getGoals().catch(() => []),
        ]);

        if (!prof) {
          // If no profile exists, redirect user to onboarding questionnaire
          router.push("/app/onboarding");
          return;
        }

        setProfile(prof);
        setAssessment(assess);
        setGoals(userGoals);
        setEditCapital(prof.investable_capital);
        setEditContribution(prof.monthly_contribution);
      } catch (err: any) {
        setError(err.message || "Failed to load financial profile");
      } finally {
        setIsLoading(false);
      }
    }

    if (user) {
      loadData();
    }
  }, [user, isAuthLoading, router]);

  const handleSaveProfileChanges = async () => {
    if (!profile) return;
    setIsSavingProfile(true);
    try {
      const updated = await updateProfile({
        investable_capital: editCapital,
        monthly_contribution: editContribution,
      });
      setProfile(updated);
      setIsEditingCapital(false);
    } catch (err: any) {
      setError(err.message || "Failed to update profile");
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingGoal(true);
    try {
      const goal = await createGoal({
        name: newGoalName,
        type: newGoalType,
        target_amount: newGoalAmount,
        target_date: newGoalDate,
        priority: goals.length + 1,
      });
      setGoals((prev) => [...prev, goal]);
      setShowAddGoal(false);
      setNewGoalName("");
      setNewGoalAmount("");
      setNewGoalDate("");
    } catch (err: any) {
      setError(err.message || "Failed to create goal");
    } finally {
      setIsSavingGoal(false);
    }
  };

  const handleDeleteGoal = async (goalId: string) => {
    try {
      await deleteGoal(goalId);
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
    } catch (err: any) {
      setError(err.message || "Failed to delete goal");
    }
  };

  if (isAuthLoading || isLoading) {
    return (
      <div className="min-h-screen bg-[#090d16] flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
      {/* Top Bar */}
      <header className="border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Link href="/app/dashboard" className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white">FinSight</span>
            </Link>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Profile & Goals
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              href="/app/dashboard"
              className="text-xs font-medium text-slate-400 hover:text-white transition px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-800/50"
            >
              Back to Dashboard
            </Link>
            <Link
              href="/app/onboarding"
              className="text-xs font-medium text-blue-400 hover:text-blue-300 transition px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/20 flex items-center space-x-1.5"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retake Questionnaire</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-10 w-full space-y-8">
        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Profile Header Card */}
        {profile && (
          <div className="p-8 rounded-3xl border border-slate-800 bg-gradient-to-b from-slate-900/60 to-slate-950/80 shadow-xl relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                    Profile Version {profile.profile_version}
                  </span>
                  {assessment && (
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold">
                      {Math.round(assessment.confidence * 100)}% Calibrated Confidence
                    </span>
                  )}
                </div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight">
                  {user?.name}&apos;s Financial Profile
                </h1>
                <p className="mt-1 text-xs text-slate-400">
                  Last updated {new Date(profile.updated_at).toLocaleDateString()} &bull; Tenant Isolation via PostgreSQL RLS
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setIsEditingCapital(!isEditingCapital)}
                  className="px-4 py-2 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-900/40 text-xs font-medium text-slate-300 hover:text-white transition flex items-center space-x-1.5"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                  <span>Update Capital / Contribution</span>
                </button>
              </div>
            </div>

            {/* Quick Edit Capital Form */}
            {isEditingCapital && (
              <div className="mt-6 p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Update Monthly Contributions & Capital
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Investable Capital ($)</label>
                    <input
                      type="number"
                      value={editCapital}
                      onChange={(e) => setEditCapital(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Monthly Contribution ($)</label>
                    <input
                      type="number"
                      value={editContribution}
                      onChange={(e) => setEditContribution(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => setIsEditingCapital(false)}
                    className="px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveProfileChanges}
                    disabled={isSavingProfile}
                    className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center space-x-1.5"
                  >
                    {isSavingProfile ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                    <span>Save Changes</span>
                  </button>
                </div>
              </div>
            )}

            {/* Dimension Highlights Grid */}
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl border border-slate-800/80 bg-slate-950/40">
                <span className="text-xs text-slate-400 block">Risk Tolerance</span>
                <span className="text-lg font-bold text-blue-400 mt-0.5 block">
                  {profile.risk_tolerance}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">Psychological appetite</span>
              </div>

              <div className="p-4 rounded-2xl border border-slate-800/80 bg-slate-950/40">
                <span className="text-xs text-slate-400 block">Risk Capacity</span>
                <span className="text-lg font-bold text-indigo-400 mt-0.5 block">
                  {profile.risk_capacity}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">Loss absorption resilience</span>
              </div>

              <div className="p-4 rounded-2xl border border-slate-800/80 bg-slate-950/40">
                <span className="text-xs text-slate-400 block">Liquidity Requirement</span>
                <span className="text-lg font-bold text-purple-400 mt-0.5 block">
                  {profile.liquidity_requirement}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">Cash access availability</span>
              </div>

              <div className="p-4 rounded-2xl border border-slate-800/80 bg-slate-950/40">
                <span className="text-xs text-slate-400 block">Capital & Deployment</span>
                <span className="text-lg font-bold text-emerald-400 mt-0.5 block">
                  ${Number(profile.investable_capital).toLocaleString()}
                </span>
                <span className="text-xs text-slate-500 mt-1 block">
                  +${Number(profile.monthly_contribution).toLocaleString()}/month
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Structured Judgment Breakdown ("How was this determined?") */}
        {assessment && (
          <div className="border border-slate-800 rounded-3xl bg-slate-900/30 overflow-hidden">
            <button
              onClick={() => setShowHowDetermined(!showHowDetermined)}
              className="w-full px-6 py-5 flex items-center justify-between hover:bg-slate-800/40 transition text-left"
            >
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Brain className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">How was this determined?</h3>
                  <p className="text-xs text-slate-400">
                    Jev System One questions, calibrated confidence, and decision probability vectors
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(assessment.jev_dimensions || {}).map(([dimKey, dim]) => (
                    <div key={dimKey} className="p-4 rounded-2xl border border-slate-800 bg-slate-950/40 space-y-3">
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
                          Choice: <span className="text-blue-400">{dim.choice_value}</span>
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
        )}

        {/* Financial Goals Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Financial Goals</h2>
              <p className="text-xs text-slate-400">Track and anchor portfolios to your concrete milestones</p>
            </div>
            <button
              onClick={() => setShowAddGoal(!showAddGoal)}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-blue-500/20"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Goal</span>
            </button>
          </div>

          {/* Add Goal Form */}
          {showAddGoal && (
            <form onSubmit={handleCreateGoal} className="p-6 rounded-3xl border border-slate-800 bg-slate-900/50 space-y-4">
              <h3 className="text-sm font-bold text-white">Create New Financial Goal</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Goal Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Retirement, House Downpayment"
                    value={newGoalName}
                    onChange={(e) => setNewGoalName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Type</label>
                  <select
                    value={newGoalType}
                    onChange={(e) => setNewGoalType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="retirement">Retirement</option>
                    <option value="real_estate">Real Estate</option>
                    <option value="emergency_fund">Emergency Fund</option>
                    <option value="education">Education</option>
                    <option value="general">General Growth</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Target Amount ($)</label>
                  <input
                    type="number"
                    placeholder="50000"
                    value={newGoalAmount}
                    onChange={(e) => setNewGoalAmount(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Target Date</label>
                  <input
                    type="date"
                    value={newGoalDate}
                    onChange={(e) => setNewGoalDate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddGoal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-800 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingGoal}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center space-x-1.5"
                >
                  {isSavingGoal ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                  <span>Save Goal</span>
                </button>
              </div>
            </form>
          )}

          {/* Goals List */}
          {goals.length === 0 ? (
            <div className="p-8 rounded-3xl border border-slate-800/80 bg-slate-900/20 text-center space-y-3">
              <Target className="h-10 w-10 text-slate-600 mx-auto" />
              <p className="text-sm text-slate-400">No financial goals defined yet.</p>
              <button
                onClick={() => setShowAddGoal(true)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium inline-flex items-center space-x-1.5"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Create your first goal</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {goals.map((g) => (
                <div key={g.id} className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4 relative flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 capitalize font-medium">
                        {g.type.replace(/_/g, " ")}
                      </span>
                      <button
                        onClick={() => handleDeleteGoal(g.id)}
                        className="text-slate-500 hover:text-rose-400 transition"
                        title="Delete Goal"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    <h3 className="text-base font-bold text-white mt-3">{g.name}</h3>

                    <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                      <span>Target: ${Number(g.target_amount).toLocaleString()}</span>
                      <span>By: {new Date(g.target_date).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-500">
                    <span>Priority {g.priority}</span>
                    <span className="text-emerald-400 capitalize">{g.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
