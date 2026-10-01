import { fetchWithAuth, formatErrorDetail } from "./auth";

export interface QuestionnaireOption {
  value: string;
  label: string;
  description?: string;
}

export interface QuestionnaireItem {
  id: string;
  category: string;
  title: string;
  description: string;
  why_it_matters: string;
  input_type: "number" | "select" | "currency";
  options?: QuestionnaireOption[];
  min_value?: number;
  max_value?: number;
  step?: number;
  unit?: string;
  required: boolean;
}

export interface JevDimensionSummary {
  question_id: string;
  result_type: string;
  choice_value?: string;
  score_value?: number;
  confidence: number;
  probabilities?: Record<string, number>;
  model_version: string;
}

export interface FinancialProfile {
  id: string;
  user_id: string;
  profile_version: number;
  risk_tolerance: string;
  risk_capacity: string;
  investment_horizon: string;
  liquidity_requirement: string;
  primary_goal: string;
  investable_capital: string;
  monthly_contribution: string;
  experience_level: string;
  esg_preference?: string;
  tax_bracket?: string;
  loss_tolerance_pct?: string;
  created_at: string;
  updated_at: string;
}

export interface ProfileAssessment {
  id: string;
  user_id: string;
  profile_id?: string;
  assessment_version: number;
  confidence: number;
  routing_action: "continue" | "gather_more_evidence" | "request_clarification" | "mark_insufficient";
  reason: string;
  follow_up_prompt?: string;
  jev_dimensions: Record<string, JevDimensionSummary>;
  created_at: string;
}

export interface ProfileWithAssessment {
  profile: FinancialProfile;
  assessment: ProfileAssessment;
}

export interface FinancialGoal {
  id: string;
  user_id: string;
  name: string;
  type: string;
  target_amount: string;
  current_amount: string;
  target_date: string;
  priority: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export async function getQuestionnaire(): Promise<QuestionnaireItem[]> {
  const res = await fetchWithAuth("/api/v1/profile/questionnaire");
  if (!res.ok) {
    throw new Error("Failed to load questionnaire");
  }
  return res.json();
}

export async function submitAssessment(answers: Record<string, any>): Promise<ProfileWithAssessment> {
  const res = await fetchWithAuth("/api/v1/profile/assessment", {
    method: "POST",
    body: JSON.stringify(answers),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    const detail = errorData ? (errorData.detail ?? errorData.message ?? errorData) : null;
    throw new Error(formatErrorDetail(detail) || "Failed to submit assessment");
  }
  return res.json();
}

export async function getProfile(): Promise<FinancialProfile | null> {
  const res = await fetchWithAuth("/api/v1/profile");
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(errorData?.detail) || "Failed to fetch financial profile");
  }
  return res.json();
}

export async function getLatestAssessment(): Promise<ProfileAssessment | null> {
  const res = await fetchWithAuth("/api/v1/profile/assessment");
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(errorData?.detail) || "Failed to fetch assessment");
  }
  return res.json();
}

export async function updateProfile(data: Partial<FinancialProfile>): Promise<FinancialProfile> {
  const res = await fetchWithAuth("/api/v1/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(errorData?.detail) || "Failed to update profile");
  }
  return res.json();
}

export async function getGoals(): Promise<FinancialGoal[]> {
  const res = await fetchWithAuth("/api/v1/goals");
  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(formatErrorDetail(errorData?.detail) || "Failed to fetch goals");
  }
  return res.json();
}

export async function createGoal(goal: {
  name: string;
  type: string;
  target_amount: string;
  target_date: string;
  priority?: number;
  current_amount?: string;
}): Promise<FinancialGoal> {
  const res = await fetchWithAuth("/api/v1/goals", {
    method: "POST",
    body: JSON.stringify(goal),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    const detail = err ? (err.detail ?? err.message ?? err) : null;
    throw new Error(formatErrorDetail(detail) || "Failed to create goal");
  }
  return res.json();
}

export async function deleteGoal(goalId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/goals/${goalId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error("Failed to delete goal");
  }
}
