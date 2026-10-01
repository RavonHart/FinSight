import { fetchWithAuth, formatErrorDetail } from "./auth";

export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  base_currency: string;
  portfolio_type: "manual" | "virtual";
  is_virtual: boolean;
  created_at: string;
  updated_at: string;
}

export interface Holding {
  id: string;
  portfolio_id: string;
  asset_id: string;
  symbol: string;
  name: string;
  asset_type: string;
  sector?: string | null;
  quantity: string;
  average_cost: string;
  current_price?: string | null;
  current_price_as_of?: string | null;
  current_value?: string | null;
  unrealized_gain_loss?: string | null;
  unrealized_gain_loss_pct?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  portfolio_id: string;
  asset_id: string;
  symbol: string;
  transaction_type: "buy" | "sell" | "dividend" | "split" | "fee_adjustment";
  quantity: string;
  price: string;
  fees: string;
  transaction_date: string;
  idempotency_key?: string | null;
  created_at: string;
}

export interface AllocationItem {
  asset_id?: string;
  symbol: string;
  name: string;
  asset_type: string;
  value: string;
  weight: string;
  weight_pct: string;
}

export interface SectorExposureItem {
  sector: string;
  value: string;
  weight: string;
  weight_pct: string;
}

export interface ConcentrationMetrics {
  top_1_weight: string;
  top_3_weight: string;
  top_5_weight: string;
  hhi: string;
  concentration_level: "diversified" | "moderately_concentrated" | "highly_concentrated";
}

export interface PortfolioAnalytics {
  portfolio_id: string;
  portfolio_name: string;
  is_virtual: boolean;
  base_currency: string;
  total_value: string;
  total_cost: string;
  unrealized_gain_loss: string;
  unrealized_gain_loss_pct?: string | null;
  holdings_count: number;
  allocations: AllocationItem[];
  sector_exposures: SectorExposureItem[];
  concentration: ConcentrationMetrics;
  annualized_return_xirr?: string | null;
}

export async function listPortfolios(): Promise<Portfolio[]> {
  const res = await fetchWithAuth("/api/v1/portfolios");
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to load portfolios");
  }
  return res.json();
}

export async function createPortfolio(data: {
  name: string;
  base_currency?: string;
  portfolio_type?: "manual" | "virtual";
  is_virtual?: boolean;
}): Promise<Portfolio> {
  const res = await fetchWithAuth("/api/v1/portfolios", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to create portfolio");
  }
  return res.json();
}

export async function getPortfolio(portfolioId: string): Promise<Portfolio> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to fetch portfolio");
  }
  return res.json();
}

export async function updatePortfolio(
  portfolioId: string,
  data: { name?: string; base_currency?: string }
): Promise<Portfolio> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to update portfolio");
  }
  return res.json();
}

export async function deletePortfolio(portfolioId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to delete portfolio");
  }
}

export async function listHoldings(portfolioId: string): Promise<Holding[]> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}/holdings`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to load holdings");
  }
  return res.json();
}

export async function createHolding(
  portfolioId: string,
  data: {
    symbol: string;
    quantity: number | string;
    average_cost: number | string;
    current_price?: number | string;
    sector?: string;
  }
): Promise<Holding> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}/holdings`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to add holding");
  }
  return res.json();
}

export async function deleteHolding(portfolioId: string, holdingId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}/holdings/${holdingId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to delete holding");
  }
}

export async function listTransactions(portfolioId: string): Promise<Transaction[]> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}/transactions`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to load transactions");
  }
  return res.json();
}

export async function recordTransaction(
  portfolioId: string,
  data: {
    symbol: string;
    transaction_type: "buy" | "sell" | "dividend" | "split" | "fee_adjustment";
    quantity: number | string;
    price: number | string;
    fees?: number | string;
    idempotency_key?: string;
  }
): Promise<Transaction> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}/transactions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to record transaction");
  }
  return res.json();
}

export async function getPortfolioAnalytics(portfolioId: string): Promise<PortfolioAnalytics> {
  const res = await fetchWithAuth(`/api/v1/portfolios/${portfolioId}/analytics`);
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(err?.detail) || "Failed to compute portfolio analytics");
  }
  return res.json();
}
