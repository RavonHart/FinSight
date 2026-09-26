export type UUID = string;
export type ISODateString = string;

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  database: "ok" | "error" | "unavailable";
  redis: "ok" | "error" | "unavailable";
  version?: string;
  timestamp?: ISODateString;
}

export interface User {
  id: UUID;
  email: string;
  name: string;
  avatar_url?: string | null;
  auth_provider: string;
  is_admin: boolean;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface FinancialProfile {
  id: UUID;
  user_id: UUID;
  investable_capital: string; // Decimal string
  monthly_contribution: string; // Decimal string
  investment_horizon: string;
  primary_goal: string;
  experience_level: string;
  liquidity_requirement: string;
  risk_tolerance?: string | null;
  risk_capacity?: string | null;
  profile_version: number;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export type PortfolioType = "manual" | "virtual";

export interface Portfolio {
  id: UUID;
  user_id: UUID;
  name: string;
  base_currency: string;
  portfolio_type: PortfolioType;
  is_virtual: boolean;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface Holding {
  id: UUID;
  portfolio_id: UUID;
  asset_id: UUID;
  quantity: string;
  average_cost: string;
  current_price?: string | null;
  current_price_as_of?: ISODateString | null;
  current_value?: string | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export type ResearchRunStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "completed_partial";

export interface ResearchRun {
  id: UUID;
  project_id: UUID;
  user_id: UUID;
  question: string;
  status: ResearchRunStatus;
  research_iterations: number;
  tool_calls_used: number;
  started_at?: ISODateString | null;
  completed_at?: ISODateString | null;
  error_message?: string | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface JevEvaluation {
  id: UUID;
  question_id: string;
  result_type: string;
  choice_value?: string | null;
  score_value?: number | null;
  probabilities?: Record<string, number> | null;
  confidence: number;
  model_version: string;
  created_at: ISODateString;
}
