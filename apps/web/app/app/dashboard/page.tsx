"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  User,
  ShieldCheck,
  Briefcase,
  Search,
  BookOpen,
  Eye,
  LogOut,
  Layers,
  Sparkles,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { useAuth } from "@/components/auth-context";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#090d16] flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 selection:bg-blue-600 selection:text-white">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white">FinSight</span>
            </Link>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Workspace
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded-full">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="font-medium text-slate-200">{user.name}</span>
              <span className="text-slate-500">({user.email})</span>
            </div>

            <button
              onClick={handleLogout}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-800/60 text-xs font-medium text-slate-400 hover:text-white transition"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Log out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-8 border-b border-slate-800/80">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Welcome back, {user.name}
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Authenticated Session &bull; Row-Level Security Protected Tenant Context
            </p>
          </div>

          <div className="mt-4 md:mt-0 flex items-center space-x-2">
            <span className="text-xs px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium flex items-center space-x-1.5">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>JWT Verified</span>
            </span>
            {user.is_admin && (
              <span className="text-xs px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-400 font-medium">
                Admin
              </span>
            )}
          </div>
        </div>

        {/* Phase Modules Grid */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Financial Profile Card */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
                <User className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Financial Profile</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Structured risk questionnaire with Jev confidence scoring and personalized financial goals.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
              <span className="text-xs text-blue-400 font-medium">Phase 2</span>
              <span className="text-xs text-slate-500">Coming next</span>
            </div>
          </div>

          {/* Portfolio Card */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                <Briefcase className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Portfolio Analysis</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Manual asset recording with deterministic pure-Python calculation of CAGR, XIRR, and asset allocations.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
              <span className="text-xs text-emerald-400 font-medium">Phase 3</span>
              <span className="text-xs text-slate-500">Coming next</span>
            </div>
          </div>

          {/* Research Workspace Card */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
                <Search className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Agentic Research</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                LangGraph-orchestrated workflows with Jev confidence judgment and immutable source provenance.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
              <span className="text-xs text-indigo-400 font-medium">Phase 4 &amp; 5</span>
              <span className="text-xs text-slate-500">Coming next</span>
            </div>
          </div>

          {/* Learning Card */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4">
                <BookOpen className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Interactive Learning</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Concept modules, interactive quizzes, and AI tutor explaining complex financial dynamics.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
              <span className="text-xs text-amber-400 font-medium">Phase 8</span>
              <span className="text-xs text-slate-500">Coming next</span>
            </div>
          </div>

          {/* Watchlists Card */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
                <Eye className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Watchlists &amp; Scans</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Scheduled Celery beat scans, trigger alerts, and automated news &amp; filing monitoring.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
              <span className="text-xs text-purple-400 font-medium">Phase 9</span>
              <span className="text-xs text-slate-500">Coming next</span>
            </div>
          </div>

          {/* User Tenant Info */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/80 to-blue-950/20 flex flex-col justify-between">
            <div>
              <div className="h-10 w-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-4">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Active Tenant Context</h3>
              <div className="mt-3 space-y-1.5 text-xs text-slate-400">
                <p><strong className="text-slate-300">User ID:</strong> <span className="font-mono text-[11px] text-blue-300">{user.id}</span></p>
                <p><strong className="text-slate-300">Auth Provider:</strong> {user.auth_provider}</p>
                <p><strong className="text-slate-300">Account Status:</strong> Active</p>
              </div>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60">
              <span className="text-xs text-emerald-400 font-medium">PostgreSQL RLS Active</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
