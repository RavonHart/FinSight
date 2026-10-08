import { fetchWithAuth } from "./auth";

export interface QuizQuestionView {
  id: string;
  question: string;
  options: string[];
}

export interface QuizQuestionFeedback {
  id: string;
  question: string;
  options: string[];
  selected_index: number;
  correct_index: number;
  is_correct: boolean;
  explanation: string;
}

export interface QuizAttemptResponse {
  id: string;
  module_id: string;
  score: string | number;
  passed: boolean;
  correct_count: number;
  total_questions: number;
  feedback: QuizQuestionFeedback[];
  created_at: string;
}

export interface LearningModuleSummary {
  id: string;
  slug: string;
  title: string;
  category: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  summary: string;
  progress: string | number;
  completed: boolean;
  last_accessed?: string | null;
}

export interface LearningModuleDetail {
  id: string;
  slug: string;
  title: string;
  category: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  summary: string;
  concept: string;
  example: string;
  eli5: string;
  quant: string;
  visual_type: string;
  key_takeaways: string[];
  quiz_questions: QuizQuestionView[];
  progress: string | number;
  completed: boolean;
  last_accessed?: string | null;
  best_score?: string | number | null;
  latest_score?: string | number | null;
}

export interface CategoryProgressItem {
  total_modules: number;
  completed_modules: number;
  average_progress: string | number;
}

export interface LearningSummary {
  total_modules: number;
  completed_modules: number;
  overall_completion_pct: string | number;
  average_quiz_score?: string | number | null;
  category_breakdown: Record<string, CategoryProgressItem>;
}

export interface AITutorResponse {
  module_slug: string;
  query: string;
  mode: string;
  explanation: string;
  concepts_referenced: string[];
  suggested_followups: string[];
  profile_context_applied: boolean;
  disclaimer: string;
}

export async function listLearningModules(
  category?: string,
  difficulty?: string
): Promise<LearningModuleSummary[]> {
  const params = new URLSearchParams();
  if (category && category !== "All") params.append("category", category);
  if (difficulty && difficulty !== "all") params.append("difficulty", difficulty);

  const url = `/api/v1/learning${params.toString() ? `?${params.toString()}` : ""}`;
  const res = await fetchWithAuth(url);
  if (!res.ok) {
    throw new Error("Failed to load learning modules");
  }
  return res.json();
}

export async function getLearningModule(slugOrId: string): Promise<LearningModuleDetail> {
  const res = await fetchWithAuth(`/api/v1/learning/${slugOrId}`);
  if (!res.ok) {
    throw new Error(`Failed to load module details for '${slugOrId}'`);
  }
  return res.json();
}

export async function submitQuiz(
  slugOrId: string,
  answers: Record<string, number>
): Promise<QuizAttemptResponse> {
  const res = await fetchWithAuth(`/api/v1/learning/${slugOrId}/quiz`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Quiz evaluation failed" }));
    throw new Error(err.detail || "Quiz evaluation failed");
  }
  return res.json();
}

export async function getQuizHistory(slugOrId: string): Promise<QuizAttemptResponse[]> {
  const res = await fetchWithAuth(`/api/v1/learning/${slugOrId}/quiz-history`);
  if (!res.ok) {
    throw new Error("Failed to load quiz history");
  }
  return res.json();
}

export async function getLearningSummary(): Promise<LearningSummary> {
  const res = await fetchWithAuth("/api/v1/learning/progress");
  if (!res.ok) {
    throw new Error("Failed to load overall learning progress");
  }
  return res.json();
}

export async function askAITutor(
  slugOrId: string,
  query: string,
  mode: "clarify" | "eli5" | "quant" | "portfolio_context" | "quiz_help" = "clarify"
): Promise<AITutorResponse> {
  const res = await fetchWithAuth(`/api/v1/learning/${slugOrId}/tutor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "AI Tutor query failed" }));
    throw new Error(err.detail || "AI Tutor request failed");
  }
  return res.json();
}
