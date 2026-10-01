from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, TypedDict, Tuple

from app.core.config import settings


class ResearchState(TypedDict, total=False):
    """
    Python-process-local LangGraph state (§15, §17).
    Carries execution state, findings, and explicit loop/budget termination fields.
    """
    user_id: str
    project_id: str
    run_id: str
    question: str
    ticker: Optional[str]

    user_profile: Dict[str, Any]
    portfolio_context: Dict[str, Any]

    research_plan: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]

    sources: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    claims: List[Dict[str, Any]]

    financial_analysis: Dict[str, Any]
    market_analysis: Dict[str, Any]
    news_analysis: Dict[str, Any]

    jev_evaluations: List[Dict[str, Any]]
    jev_confidence: float
    jev_routing_action: str
    jev_routing_reason: str
    is_insufficient_test: bool
    simulation_results: Dict[str, Any]

    quality_checks: Dict[str, Any]
    report: Dict[str, Any]
    errors: List[str]
    status: str

    # Loop / budget control (§17 "Loop termination")
    research_iterations: int
    tool_calls_used: int
    run_deadline_at: str  # ISO-8601 UTC timestamp


def get_remaining_seconds(state: ResearchState) -> float:
    """Calculates remaining wall-clock seconds until run_deadline_at (§17)."""
    deadline_str = state.get("run_deadline_at")
    if not deadline_str:
        return float(settings.RUN_TIMEOUT_SECONDS)
    try:
        deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
        remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, remaining)
    except Exception:
        return float(settings.RUN_TIMEOUT_SECONDS)


def is_deadline_exceeded(state: ResearchState) -> bool:
    """Checks whether the wall-clock deadline has passed (§17)."""
    return get_remaining_seconds(state) <= 0.05


def is_tool_budget_exceeded(state: ResearchState) -> bool:
    """Checks whether tool calls exceed MAX_TOOL_CALLS ceiling (§17)."""
    return state.get("tool_calls_used", 0) >= settings.MAX_TOOL_CALLS


def is_iteration_limit_reached(state: ResearchState) -> bool:
    """Checks whether research iterations exceed MAX_RESEARCH_ITERATIONS (§17)."""
    return state.get("research_iterations", 0) >= settings.MAX_RESEARCH_ITERATIONS


def should_exit_early(state: ResearchState) -> Tuple[bool, Optional[str]]:
    """
    Evaluates guardrail limits mid-run and at decision boundaries (§17).
    Returns (should_exit, reason).
    """
    if is_deadline_exceeded(state):
        return True, "Wall-clock run deadline elapsed"
    if is_tool_budget_exceeded(state):
        return True, f"Maximum tool call budget ({settings.MAX_TOOL_CALLS}) reached"
    return False, None
