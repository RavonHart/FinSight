import { getApiBase, fetchWithAuth } from "./auth";

export interface YearlySnapshot {
  year: number;
  starting_balance: number;
  contributions: number;
  withdrawals: number;
  investment_growth: number;
  fees_paid: number;
  ending_nominal_value: number;
  ending_real_value: number;
}

export interface ScenarioResult {
  engine_version: string;
  duration_years: number;
  initial_capital: number;
  total_contributions: number;
  total_withdrawals: number;
  total_fees_paid: number;
  nominal_ending_value: number;
  real_ending_value: number;
  total_gain: number;
  is_depleted: boolean;
  depletion_year?: number | null;
  yearly_snapshots: YearlySnapshot[];
}

export interface ScenarioDefinition {
  label: string;
  assumptions: {
    annual_return_pct: number;
    annual_inflation_pct: number;
    annual_fee?: number;
  };
  result: ScenarioResult;
}

export interface SimulationResultJson {
  engine_version: string;
  inputs: Record<string, any>;
  scenarios: {
    bear: ScenarioDefinition;
    base: ScenarioDefinition;
    bull: ScenarioDefinition;
  };
}

export interface SimulationRequest {
  portfolio_id?: string | null;
  initial_capital: number;
  monthly_contribution: number;
  duration_years: number;
  annual_return_pct: number;
  annual_inflation_pct: number;
  annual_fee_pct: number;
  annual_withdrawal: number;
}

export interface SimulationRun {
  id: string;
  user_id: string;
  portfolio_id?: string | null;
  engine_version: string;
  input_json: SimulationRequest;
  result_json: SimulationResultJson;
  created_at: string;
}

export async function createSimulation(data: SimulationRequest): Promise<SimulationRun> {
  const res = await fetchWithAuth("/api/v1/simulations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to run simulation" }));
    throw new Error(err.detail || "Simulation failed");
  }

  return res.json();
}

export async function getSimulation(id: string): Promise<SimulationRun> {
  const res = await fetchWithAuth(`/api/v1/simulations/${id}`);
  if (!res.ok) {
    throw new Error("Failed to load simulation run");
  }
  return res.json();
}

export async function listSimulations(): Promise<SimulationRun[]> {
  const res = await fetchWithAuth("/api/v1/simulations");
  if (!res.ok) {
    throw new Error("Failed to list simulation runs");
  }
  return res.json();
}
