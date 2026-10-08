import { fetchWithAuth, formatErrorDetail } from "./auth";

export interface WatchlistSummary {
  id: string;
  user_id: string;
  name: string;
  scan_enabled: boolean;
  scan_frequency: string | null;
  items_count: number;
  latest_scan: WatchlistScan | null;
  created_at: string;
}

export interface WatchlistItem {
  id: string;
  watchlist_id: string;
  asset_id: string;
  ticker: string;
  name: string;
  asset_class: string;
  current_price: number | null;
  created_at: string;
}

export interface WatchlistScanFinding {
  asset_id: string;
  ticker: string;
  name: string;
  signal_type: "momentum_shift" | "valuation_compression" | "drawdown_alert" | "volatility_spike";
  severity: "low" | "medium" | "high";
  summary: string;
  details: string;
  metrics: Record<string, any>;
}

export interface WatchlistScan {
  id: string;
  watchlist_id: string;
  status: "queued" | "running" | "completed" | "failed";
  findings_count: number;
  findings: WatchlistScanFinding[];
  error_message: string | null;
  idempotency_key: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface WatchlistDetail extends WatchlistSummary {
  items: WatchlistItem[];
  scans: WatchlistScan[];
}

export interface NotificationItem {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  body: string;
  related_resource_type: string | null;
  related_resource_id: string | null;
  read_at: string | null;
  delivered_at: string | null;
  created_at: string;
}

export interface NotificationSummary {
  total_unread: number;
  notifications: NotificationItem[];
}

export async function listWatchlists(): Promise<WatchlistSummary[]> {
  const res = await fetchWithAuth("/api/v1/watchlists");
  if (!res.ok) throw new Error("Failed to fetch watchlists");
  return res.json();
}

export async function getWatchlistDetail(id: string): Promise<WatchlistDetail> {
  const res = await fetchWithAuth(`/api/v1/watchlists/${id}`);
  if (!res.ok) throw new Error("Failed to fetch watchlist details");
  return res.json();
}

export async function createWatchlist(data: {
  name: string;
  scan_enabled?: boolean;
  scan_frequency?: string;
}): Promise<WatchlistSummary> {
  const res = await fetchWithAuth("/api/v1/watchlists", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to create watchlist" }));
    throw new Error(formatErrorDetail(err.detail) || "Failed to create watchlist");
  }
  return res.json();
}

export async function deleteWatchlist(id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/watchlists/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete watchlist");
}

export async function addWatchlistItem(
  watchlistId: string,
  ticker: string
): Promise<WatchlistItem> {
  const res = await fetchWithAuth(`/api/v1/watchlists/${watchlistId}/items`, {
    method: "POST",
    body: JSON.stringify({ ticker: ticker.trim().toUpperCase() }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to add asset" }));
    throw new Error(formatErrorDetail(err.detail) || "Failed to add asset to watchlist");
  }
  return res.json();
}

export async function removeWatchlistItem(
  watchlistId: string,
  itemId: string
): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/watchlists/${watchlistId}/items/${itemId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to remove item");
}

export async function triggerWatchlistScan(
  watchlistId: string,
  idempotencyKey?: string
): Promise<WatchlistScan> {
  const headers: Record<string, string> = {};
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }
  const res = await fetchWithAuth(`/api/v1/watchlists/${watchlistId}/scan?run_sync=true`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to trigger scan" }));
    throw new Error(formatErrorDetail(err.detail) || "Failed to trigger watchlist scan");
  }
  return res.json();
}

export async function listNotifications(unreadOnly = false): Promise<NotificationSummary> {
  const res = await fetchWithAuth(`/api/v1/notifications?unread_only=${unreadOnly}`);
  if (!res.ok) throw new Error("Failed to fetch notifications");
  return res.json();
}

export async function markNotificationsRead(notificationIds?: string[]): Promise<void> {
  const res = await fetchWithAuth("/api/v1/notifications/mark-read", {
    method: "POST",
    body: JSON.stringify({ notification_ids: notificationIds || null }),
  });
  if (!res.ok) throw new Error("Failed to mark notifications read");
}
