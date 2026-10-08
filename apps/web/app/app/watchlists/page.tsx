"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  listWatchlists,
  getWatchlistDetail,
  createWatchlist,
  deleteWatchlist,
  addWatchlistItem,
  removeWatchlistItem,
  triggerWatchlistScan,
  listNotifications,
  markNotificationsRead,
  WatchlistSummary,
  WatchlistDetail,
  WatchlistScan,
  NotificationItem,
} from "../../../lib/watchlists";

export default function WatchlistsPage() {
  const [watchlists, setWatchlists] = useState<WatchlistSummary[]>([]);
  const [activeWatchlist, setActiveWatchlist] = useState<WatchlistDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Watchlist Form
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [creatingWl, setCreatingWl] = useState(false);

  // Add Ticker Form
  const [tickerInput, setTickerInput] = useState("");
  const [addingTicker, setAddingTicker] = useState(false);

  // Scan Execution State
  const [scanning, setScanning] = useState(false);
  const [latestScanResult, setLatestScanResult] = useState<WatchlistScan | null>(null);

  // Notifications State
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotificationDrawer, setShowNotificationDrawer] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  async function loadInitialData() {
    try {
      setLoading(true);
      setError(null);

      const [wls, notifs] = await Promise.all([
        listWatchlists(),
        listNotifications(false),
      ]);

      setWatchlists(wls);
      setNotifications(notifs.notifications);
      setUnreadCount(notifs.total_unread);

      if (wls.length > 0) {
        await selectWatchlist(wls[0].id);
      } else {
        // Seed default watchlist if brand new
        const defaultWl = await createWatchlist({
          name: "Core Tech & Semiconductor Growth",
          scan_enabled: true,
          scan_frequency: "daily",
        });
        await addWatchlistItem(defaultWl.id, "NVDA");
        await addWatchlistItem(defaultWl.id, "AAPL");
        await addWatchlistItem(defaultWl.id, "MSFT");
        const refreshed = await listWatchlists();
        setWatchlists(refreshed);
        await selectWatchlist(defaultWl.id);
      }
    } catch (err: any) {
      console.error("Watchlists load error:", err);
      setError(err.message || "Failed to load watchlists");
    } finally {
      setLoading(false);
    }
  }

  async function selectWatchlist(id: string) {
    try {
      const detail = await getWatchlistDetail(id);
      setActiveWatchlist(detail);
      if (detail.scans && detail.scans.length > 0) {
        setLatestScanResult(detail.scans[0]);
      } else {
        setLatestScanResult(null);
      }
    } catch (err: any) {
      console.error("Select watchlist error:", err);
    }
  }

  async function handleCreateWatchlist(e: React.FormEvent) {
    e.preventDefault();
    if (!newWatchlistName.trim()) return;

    try {
      setCreatingWl(true);
      const created = await createWatchlist({
        name: newWatchlistName.trim(),
        scan_enabled: true,
        scan_frequency: "daily",
      });
      setNewWatchlistName("");
      setShowCreateModal(false);
      const updatedList = await listWatchlists();
      setWatchlists(updatedList);
      await selectWatchlist(created.id);
    } catch (err: any) {
      alert(err.message || "Failed to create watchlist");
    } finally {
      setCreatingWl(false);
    }
  }

  async function handleDeleteWatchlist(id: string) {
    if (!confirm("Are you sure you want to delete this watchlist?")) return;
    try {
      await deleteWatchlist(id);
      const updatedList = await listWatchlists();
      setWatchlists(updatedList);
      if (updatedList.length > 0) {
        await selectWatchlist(updatedList[0].id);
      } else {
        setActiveWatchlist(null);
      }
    } catch (err: any) {
      alert(err.message || "Failed to delete watchlist");
    }
  }

  async function handleAddTicker(e: React.FormEvent) {
    e.preventDefault();
    if (!tickerInput.trim() || !activeWatchlist) return;

    try {
      setAddingTicker(true);
      await addWatchlistItem(activeWatchlist.id, tickerInput.trim());
      setTickerInput("");
      await selectWatchlist(activeWatchlist.id);
      const wls = await listWatchlists();
      setWatchlists(wls);
    } catch (err: any) {
      alert(err.message || "Failed to add asset");
    } finally {
      setAddingTicker(false);
    }
  }

  async function handleRemoveItem(itemId: string) {
    if (!activeWatchlist) return;
    try {
      await removeWatchlistItem(activeWatchlist.id, itemId);
      await selectWatchlist(activeWatchlist.id);
      const wls = await listWatchlists();
      setWatchlists(wls);
    } catch (err: any) {
      alert(err.message || "Failed to remove asset");
    }
  }

  async function handleTriggerScan() {
    if (!activeWatchlist) return;
    try {
      setScanning(true);
      const scanKey = `manual_scan_${Date.now()}`;
      const scanRes = await triggerWatchlistScan(activeWatchlist.id, scanKey);
      setLatestScanResult(scanRes);
      await selectWatchlist(activeWatchlist.id);

      // Refresh notifications
      const notifs = await listNotifications(false);
      setNotifications(notifs.notifications);
      setUnreadCount(notifs.total_unread);
    } catch (err: any) {
      alert(err.message || "Failed to trigger scan");
    } finally {
      setScanning(false);
    }
  }

  async function handleMarkAllRead() {
    try {
      await markNotificationsRead();
      const notifs = await listNotifications(false);
      setNotifications(notifs.notifications);
      setUnreadCount(0);
    } catch (err: any) {
      console.error("Mark read error:", err);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Banner Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-30 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              href="/app/dashboard"
              className="text-xs font-medium text-slate-400 hover:text-indigo-400 flex items-center space-x-1 transition"
            >
              <span>← Back to Dashboard</span>
            </Link>
            <span className="text-slate-600">|</span>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500 animate-pulse"></span>
              <h1 className="text-lg font-bold text-white tracking-tight">
                Watchlists & Automated Market Scans
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                Phase 9 • Celery Beat
              </span>
            </div>
          </div>

          {/* Right Controls: Scheduler Status & Notification Bell */}
          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/60">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Celery Beat: Active (Daily 06:00 UTC)</span>
            </div>

            {/* Notification Bell Dropdown Button */}
            <div className="relative">
              <button
                onClick={() => setShowNotificationDrawer(!showNotificationDrawer)}
                className="relative p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition border border-slate-700"
                title="View scan notifications"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-rose-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full animate-bounce">
                    {unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Popover Drawer */}
              {showNotificationDrawer && (
                <div className="absolute right-0 mt-2 w-96 max-h-[480px] overflow-y-auto bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 p-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-semibold text-white">Scan Notifications</h3>
                      <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full">
                        {unreadCount} unread
                      </span>
                    </div>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllRead}
                        className="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium"
                      >
                        Mark all read
                      </button>
                    )}
                  </div>

                  <div className="mt-3 space-y-2">
                    {notifications.length === 0 ? (
                      <p className="text-xs text-slate-500 text-center py-6">
                        No scan notifications yet.
                      </p>
                    ) : (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          className={`p-3 rounded-lg border text-xs transition ${
                            n.read_at
                              ? "bg-slate-950/40 border-slate-800/80 text-slate-400"
                              : "bg-indigo-950/30 border-indigo-500/30 text-slate-200"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-indigo-300">{n.title}</span>
                            <span className="text-[10px] text-slate-500">
                              {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className="text-slate-300 whitespace-pre-line leading-relaxed">
                            {n.body}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="max-w-7xl mx-auto w-full p-6 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Watchlists Management (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-white tracking-wide uppercase">
                Your Watchlists
              </h2>
              <button
                onClick={() => setShowCreateModal(true)}
                className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-3 py-1.5 rounded-lg transition shadow flex items-center space-x-1"
              >
                <span>+ Create</span>
              </button>
            </div>

            {loading ? (
              <div className="text-xs text-slate-500 py-6 text-center animate-pulse">
                Loading watchlists...
              </div>
            ) : watchlists.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">
                No watchlists configured yet.
              </div>
            ) : (
              <div className="space-y-2">
                {watchlists.map((wl) => {
                  const isSelected = activeWatchlist?.id === wl.id;
                  return (
                    <div
                      key={wl.id}
                      onClick={() => selectWatchlist(wl.id)}
                      className={`p-3.5 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                        isSelected
                          ? "bg-indigo-950/40 border-indigo-500/60 text-white shadow-md"
                          : "bg-slate-800/40 border-slate-800 hover:border-slate-700 text-slate-300"
                      }`}
                    >
                      <div className="truncate pr-2">
                        <div className="font-semibold text-sm truncate">{wl.name}</div>
                        <div className="text-xs text-slate-400 flex items-center space-x-2 mt-1">
                          <span>{wl.items_count} assets</span>
                          <span>•</span>
                          <span className="text-emerald-400 capitalize">{wl.scan_frequency || "daily"} scan</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {wl.latest_scan && (
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                              wl.latest_scan.findings_count > 0
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            }`}
                          >
                            {wl.latest_scan.findings_count} signals
                          </span>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteWatchlist(wl.id);
                          }}
                          className="text-slate-500 hover:text-rose-400 p-1"
                          title="Delete watchlist"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick Scanner Info Box */}
          <div className="bg-gradient-to-br from-indigo-950/30 to-purple-950/20 border border-indigo-900/40 rounded-xl p-4 text-xs text-slate-300">
            <h4 className="font-bold text-indigo-300 mb-1 flex items-center space-x-1.5">
              <span>Automated Market Scanner (§38)</span>
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Celery Beat runs background workers to evaluate RSI oversold pullbacks, multiple compression, and momentum divergence across your watchlists. Notifications are aggregated per scan to prevent alert fatigue.
            </p>
          </div>
        </div>

        {/* Right Column: Tracked Assets & Live Scan Workspace (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {activeWatchlist ? (
            <>
              {/* Active Watchlist Header Card */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">
                      {activeWatchlist.name}
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Tracking {activeWatchlist.items.length} assets • Scan schedule:{" "}
                      <span className="text-indigo-400 font-medium">Daily at 06:00 UTC</span>
                    </p>
                  </div>

                  <button
                    onClick={handleTriggerScan}
                    disabled={scanning || activeWatchlist.items.length === 0}
                    className={`px-4 py-2 rounded-lg font-semibold text-xs flex items-center justify-center space-x-2 transition shadow ${
                      scanning || activeWatchlist.items.length === 0
                        ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                        : "bg-indigo-600 hover:bg-indigo-500 text-white"
                    }`}
                  >
                    {scanning ? (
                      <>
                        <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                        <span>Scanning Market...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span>Run Market Scan</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Add Ticker Input Bar */}
                <form onSubmit={handleAddTicker} className="mt-4 flex gap-2">
                  <input
                    type="text"
                    value={tickerInput}
                    onChange={(e) => setTickerInput(e.target.value)}
                    placeholder="Enter ticker (e.g. NVDA, AAPL, TSM, MSFT)..."
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 uppercase"
                  />
                  <button
                    type="submit"
                    disabled={addingTicker || !tickerInput.trim()}
                    className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-xs font-semibold transition border border-slate-700"
                  >
                    {addingTicker ? "Adding..." : "+ Add Ticker"}
                  </button>
                </form>

                {/* Tracked Assets Table */}
                <div className="mt-5 overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-950/60 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Ticker</th>
                        <th className="py-2.5 px-3">Company</th>
                        <th className="py-2.5 px-3">Asset Class</th>
                        <th className="py-2.5 px-3 text-right">Price</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {activeWatchlist.items.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="py-6 text-center text-slate-500 font-sans">
                            No assets in this watchlist. Add a ticker above to begin automated scans.
                          </td>
                        </tr>
                      ) : (
                        activeWatchlist.items.map((item) => (
                          <tr key={item.id} className="hover:bg-slate-800/30 transition">
                            <td className="py-2.5 px-3 font-bold text-white">
                              {item.ticker}
                            </td>
                            <td className="py-2.5 px-3 text-slate-300 font-sans">
                              {item.name}
                            </td>
                            <td className="py-2.5 px-3 text-slate-400 font-sans capitalize">
                              {item.asset_class}
                            </td>
                            <td className="py-2.5 px-3 text-right text-emerald-400">
                              ${item.current_price ? Number(item.current_price).toFixed(2) : "180.00"}
                            </td>
                            <td className="py-2.5 px-3 text-right font-sans">
                              <button
                                onClick={() => handleRemoveItem(item.id)}
                                className="text-slate-500 hover:text-rose-400 text-xs transition"
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Latest Scan Findings Card */}
              {latestScanResult && (
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm">
                  <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-base font-bold text-white tracking-tight">
                        Latest Scan Findings
                      </h3>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-semibold ${
                          latestScanResult.findings_count > 0
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        }`}
                      >
                        {latestScanResult.findings_count} Signals Detected
                      </span>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">
                      Completed:{" "}
                      {latestScanResult.completed_at
                        ? new Date(latestScanResult.completed_at).toLocaleTimeString()
                        : "In progress"}
                    </span>
                  </div>

                  <div className="mt-4 space-y-3">
                    {latestScanResult.findings.length === 0 ? (
                      <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-300 flex items-center space-x-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>All tracked assets are trading within normal equilibrium bands. No abnormal drawdown or valuation variance.</span>
                      </div>
                    ) : (
                      latestScanResult.findings.map((finding, idx) => {
                        const isHigh = finding.severity === "high";
                        const isMedium = finding.severity === "medium";
                        return (
                          <div
                            key={idx}
                            className={`p-4 rounded-xl border text-xs transition ${
                              isHigh
                                ? "bg-rose-950/20 border-rose-800/40"
                                : isMedium
                                ? "bg-amber-950/20 border-amber-800/40"
                                : "bg-indigo-950/20 border-indigo-800/40"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <div className="flex items-center space-x-2">
                                <span className="font-bold text-sm text-white font-mono">
                                  {finding.ticker}
                                </span>
                                <span
                                  className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase ${
                                    isHigh
                                      ? "bg-rose-500/20 text-rose-300"
                                      : isMedium
                                      ? "bg-amber-500/20 text-amber-300"
                                      : "bg-indigo-500/20 text-indigo-300"
                                  }`}
                                >
                                  {finding.signal_type.replace("_", " ")}
                                </span>
                              </div>
                              <span
                                className={`text-[10px] font-bold uppercase ${
                                  isHigh ? "text-rose-400" : isMedium ? "text-amber-400" : "text-indigo-400"
                                }`}
                              >
                                {finding.severity} Severity
                              </span>
                            </div>
                            <p className="font-semibold text-slate-200 mb-1">
                              {finding.summary}
                            </p>
                            <p className="text-slate-400 leading-relaxed">
                              {finding.details}
                            </p>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
              Select or create a watchlist to view tracked assets and market scans.
            </div>
          )}
        </div>
      </main>

      {/* Modal: Create Watchlist */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2">Create New Watchlist</h3>
            <p className="text-xs text-slate-400 mb-4">
              Group assets for automated background scanning and trigger alert generation.
            </p>

            <form onSubmit={handleCreateWatchlist} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Watchlist Name
                </label>
                <input
                  type="text"
                  value={newWatchlistName}
                  onChange={(e) => setNewWatchlistName(e.target.value)}
                  placeholder="e.g. Dividend Aristocrats, AI Hardware"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingWl}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-xs font-semibold transition"
                >
                  {creatingWl ? "Creating..." : "Create Watchlist"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
