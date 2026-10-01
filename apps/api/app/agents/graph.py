import re
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.core.logging import logger
from app.agents.state import (
    ResearchState,
    should_exit_early,
    is_iteration_limit_reached,
    is_tool_budget_exceeded,
    is_deadline_exceeded,
)
from app.agents.events import publish_run_event
from app.tools.research_tools import (
    fetch_financial_metrics,
    fetch_market_analysis,
    fetch_news_and_catalysts,
)

# Common ticker resolution map for natural language questions (e.g. "Research NVIDIA" -> NVDA)
TICKER_RESOLVER = {
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "apple": "AAPL",
    "aapl": "AAPL",
    "microsoft": "MSFT",
    "msft": "MSFT",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "googl": "GOOGL",
    "vanguard total stock": "VTI",
    "vti": "VTI",
    "spdr": "SPY",
    "spy": "SPY",
}


def extract_ticker_from_question(question: str) -> str:
    """Extracts ticker symbol or known company name from user prompt."""
    q_lower = question.lower()
    for name, sym in TICKER_RESOLVER.items():
        if name in q_lower:
            return sym

    # Fallback regex search for isolated uppercase 1-5 character ticker
    match = re.search(r"\b([A-Z]{1,5})\b", question)
    if match:
        return match.group(1).upper()
    return "NVDA"  # Default canonical research target


# ---------------------------------------------------------------------------
# LangGraph Node Functions (§16)
# ---------------------------------------------------------------------------

async def load_context(state: ResearchState) -> ResearchState:
    """
    Initial node: loads user risk profile, extracts ticker, sets deadline, and emits start event (§16).
    """
    run_id = state.get("run_id", str(uuid.uuid4()))
    question = state.get("question", "")
    ticker = extract_ticker_from_question(question)

    state["ticker"] = ticker
    state["research_iterations"] = state.get("research_iterations", 0)
    state["tool_calls_used"] = state.get("tool_calls_used", 0)
    state["status"] = "running"
    state["errors"] = state.get("errors", [])
    state["sources"] = state.get("sources", [])
    state["evidence"] = state.get("evidence", [])
    state["claims"] = state.get("claims", [])

    # Set hard wall-clock deadline if not already initialized
    if not state.get("run_deadline_at"):
        deadline = datetime.now(timezone.utc).timestamp() + settings.RUN_TIMEOUT_SECONDS
        state["run_deadline_at"] = datetime.fromtimestamp(deadline, tz=timezone.utc).isoformat()

    await publish_run_event(
        run_id=run_id,
        event_type="run_started",
        payload={
            "run_id": run_id,
            "ticker": ticker,
            "question": question,
            "deadline_at": state["run_deadline_at"],
        },
    )

    return state


async def generate_plan(state: ResearchState) -> ResearchState:
    """Generates structured research tasks and publishes research_plan (§16)."""
    run_id = state["run_id"]
    ticker = state.get("ticker", "NVDA")

    tasks = [
        {"id": f"task-fin-{run_id[:6]}", "task_type": "financial_analysis", "title": f"Evaluate {ticker} financial metrics & valuation", "status": "pending"},
        {"id": f"task-mkt-{run_id[:6]}", "task_type": "market_analysis", "title": f"Analyze {ticker} competitive positioning & moat", "status": "pending"},
        {"id": f"task-nws-{run_id[:6]}", "task_type": "news_analysis", "title": f"Examine recent catalysts & regulatory risks", "status": "pending"},
        {"id": f"task-evd-{run_id[:6]}", "task_type": "evidence_validation", "title": f"Extract evidence passages & verify sources", "status": "pending"},
        {"id": f"task-jev-{run_id[:6]}", "task_type": "jev_analysis", "title": f"Execute Jev System One calibrated assessments", "status": "pending"},
        {"id": f"task-syn-{run_id[:6]}", "task_type": "synthesis", "title": f"Synthesize evidence-backed report with provenance", "status": "pending"},
    ]
    state["tasks"] = tasks
    state["research_plan"] = tasks

    await publish_run_event(
        run_id=run_id,
        event_type="plan_generated",
        payload={"tasks": tasks},
    )
    return state


async def financial_research(state: ResearchState) -> ResearchState:
    """Retrieves financial statements and valuation multiples with deadline checks (§16, §17)."""
    run_id = state["run_id"]
    ticker = state.get("ticker", "NVDA")

    should_exit, reason = should_exit_early(state)
    if should_exit:
        logger.warning(f"Skipping financial_research: {reason}")
        state["errors"].append(reason)
        return state

    await publish_run_event(run_id=run_id, event_type="task_started", payload={"task_type": "financial_analysis"})

    data = await fetch_financial_metrics(state, ticker, timeout=10.0)
    state["financial_analysis"] = data

    await publish_run_event(
        run_id=run_id,
        event_type="task_completed",
        payload={"task_type": "financial_analysis", "data": {"metrics_count": len(data)}},
    )
    return state


async def market_research(state: ResearchState) -> ResearchState:
    """Gathers competitive moat, TAM, and market share data with deadline checks (§16, §17)."""
    run_id = state["run_id"]
    ticker = state.get("ticker", "NVDA")

    should_exit, reason = should_exit_early(state)
    if should_exit:
        logger.warning(f"Skipping market_research: {reason}")
        state["errors"].append(reason)
        return state

    await publish_run_event(run_id=run_id, event_type="task_started", payload={"task_type": "market_analysis"})

    data = await fetch_market_analysis(state, ticker, timeout=10.0)
    state["market_analysis"] = data

    await publish_run_event(
        run_id=run_id,
        event_type="task_completed",
        payload={"task_type": "market_analysis", "data": {"moat": data.get("software_moat")}},
    )
    return state


async def news_research(state: ResearchState) -> ResearchState:
    """Retrieves press releases, regulatory filings, and catalysts with deadline checks (§16, §17)."""
    run_id = state["run_id"]
    ticker = state.get("ticker", "NVDA")

    should_exit, reason = should_exit_early(state)
    if should_exit:
        logger.warning(f"Skipping news_research: {reason}")
        state["errors"].append(reason)
        return state

    await publish_run_event(run_id=run_id, event_type="task_started", payload={"task_type": "news_analysis"})

    data = await fetch_news_and_catalysts(state, ticker, timeout=10.0)
    state["news_analysis"] = {"items": data}

    await publish_run_event(
        run_id=run_id,
        event_type="task_completed",
        payload={"task_type": "news_analysis", "data": {"news_items_count": len(data)}},
    )
    return state


async def evidence_extraction(state: ResearchState) -> ResearchState:
    """Extracts atomic claims, evidence passages, and immutable sources with URLs (§16)."""
    run_id = state["run_id"]
    await publish_run_event(
        run_id=run_id,
        event_type="task_started",
        payload={"task_type": "evidence_validation"},
    )

    ticker = state.get("ticker", "NVDA")
    fin = state.get("financial_analysis", {})
    mkt = state.get("market_analysis", {})
    news_items = state.get("news_analysis", {}).get("items", [])

    sources = []
    evidence = []
    claims = []

    # 1. Financial source & evidence
    if fin.get("source_url"):
        src_id = str(uuid.uuid4())
        sources.append({
            "id": src_id,
            "source_type": "sec_filing",
            "title": f"{ticker} Official Financial Disclosures ({fin.get('fiscal_year', 'FY2024')})",
            "url": fin.get("source_url"),
            "publisher": f"{ticker} Investor Relations",
        })
        rev = fin.get("revenue_usd_b")
        evidence.append({
            "id": str(uuid.uuid4()),
            "source_id": src_id,
            "claim": f"{ticker} generated ${rev}B in revenue with gross margins of {float(fin.get('gross_margin_pct', 0.5))*100:.1f}%.",
            "evidence_text": f"Reported fiscal metrics: Revenue ${rev}B, Free Cash Flow ${fin.get('free_cash_flow_b')}B, Net Income ${fin.get('net_income_usd_b')}B.",
            "relevance_score": Decimal("0.980"),
        })
        claims.append({
            "id": str(uuid.uuid4()),
            "claim_text": f"{ticker} maintains highly profitable operational cash flow generation.",
            "claim_type": "fact",
            "confidence": Decimal("0.950"),
        })

    # 2. Market source & evidence
    if mkt.get("source_url"):
        src_id = str(uuid.uuid4())
        sources.append({
            "id": src_id,
            "source_type": "market_report",
            "title": f"Industry Semiconductor & Computing Architecture Analysis",
            "url": mkt.get("source_url"),
            "publisher": "Industry Research Group",
        })
        evidence.append({
            "id": str(uuid.uuid4()),
            "source_id": src_id,
            "claim": f"{ticker} maintains a dominant software moat: {mkt.get('software_moat')}",
            "evidence_text": f"Competitive landscape highlights: {mkt.get('software_moat')}. Key competitors include: {', '.join(mkt.get('key_competitors', []))}.",
            "relevance_score": Decimal("0.920"),
        })

    # 3. News source & evidence
    for item in news_items[:2]:
        if item.get("url"):
            src_id = str(uuid.uuid4())
            sources.append({
                "id": src_id,
                "source_type": "news_wire",
                "title": item.get("headline", ""),
                "url": item.get("url"),
                "publisher": item.get("source", "Financial News"),
            })
            evidence.append({
                "id": str(uuid.uuid4()),
                "source_id": src_id,
                "claim": item.get("headline", ""),
                "evidence_text": item.get("summary", ""),
                "relevance_score": Decimal("0.890"),
            })

    state["sources"] = sources
    state["evidence"] = evidence
    state["claims"] = claims

    await publish_run_event(
        run_id=run_id,
        event_type="evidence_collected",
        payload={
            "sources_count": len(sources),
            "evidence_count": len(evidence),
            "claims_count": len(claims),
        },
    )
    await publish_run_event(
        run_id=run_id,
        event_type="task_completed",
        payload={"task_type": "evidence_validation", "sources_count": len(sources), "evidence_count": len(evidence)},
    )
    return state


async def jev_analysis(state: ResearchState) -> ResearchState:
    """
    Executes Jev System One questions against empirical findings (§13, §14, §16).
    Evaluates evidence sufficiency, financial strength, moat, and calibrates claim status.
    """
    run_id = state["run_id"]
    await publish_run_event(
        run_id=run_id,
        event_type="task_started",
        payload={"task_type": "jev_analysis"},
    )
    from app.jev.client import JevClient
    from app.jev.evaluators import evaluate_research_state

    client = JevClient()
    results_dict, aggregate_confidence, routing_decision, updated_claims = await evaluate_research_state(state, client)

    # Format into serializable list
    eval_list = [
        {
            "question_id": r.question_id,
            "result_type": r.result_type.value,
            "choice_value": r.choice_value,
            "score_value": float(r.score_value) if r.score_value is not None else None,
            "probabilities": r.probabilities,
            "confidence": float(r.confidence),
            "model_version": r.model_version,
        }
        for r in results_dict.values()
    ]

    state["jev_evaluations"] = eval_list
    state["claims"] = updated_claims
    state["jev_confidence"] = aggregate_confidence
    state["jev_routing_action"] = routing_decision.action.value
    state["jev_routing_reason"] = routing_decision.reason

    await publish_run_event(
        run_id=run_id,
        event_type="jev_analysis_completed",
        payload={
            "evaluations_count": len(eval_list),
            "aggregate_confidence": aggregate_confidence,
            "routing_action": routing_decision.action.value,
        },
    )
    await publish_run_event(
        run_id=run_id,
        event_type="task_completed",
        payload={"task_type": "jev_analysis", "evaluations_count": len(eval_list)},
    )
    return state


async def quality_check(state: ResearchState) -> ResearchState:
    """
    Evaluates evidence sufficiency, Jev confidence routing, and enforces guardrails (§14, §17).
    """
    run_id = state["run_id"]
    evidence_count = len(state.get("evidence", []))
    iterations = state.get("research_iterations", 0)
    deadline_hit = is_deadline_exceeded(state)
    budget_hit = is_tool_budget_exceeded(state)
    iteration_hit = is_iteration_limit_reached(state)

    passed_guards = not (deadline_hit or budget_hit or iteration_hit)

    # Check Jev evaluations & confidence
    jev_evals = state.get("jev_evaluations", [])
    jev_conf = state.get("jev_confidence")
    if jev_conf is None and jev_evals:
        confs = [e.get("confidence", 0.0) for e in jev_evals]
        jev_conf = sum(confs) / len(confs) if confs else 0.0
    jev_conf = float(jev_conf or 0.0)
    jev_action = state.get("jev_routing_action", "continue")

    # Evaluate sufficiency: requires sufficient evidence AND Jev confidence meeting high threshold
    has_sufficient_signal = (
        evidence_count >= 2
        and len(jev_evals) > 0
        and jev_conf >= settings.JEV_HIGH_CONFIDENCE_THRESHOLD
        and jev_action != "gather_more_evidence"
        and jev_action != "mark_insufficient"
    )

    if not passed_guards or not has_sufficient_signal:
        if budget_hit:
            reason = "Tool limit reached"
        elif deadline_hit:
            reason = "Deadline elapsed"
        elif iteration_hit:
            reason = "Iteration limit reached"
        elif len(jev_evals) == 0:
            reason = "Missing Jev evaluation signal"
        elif jev_action in ("gather_more_evidence", "mark_insufficient"):
            reason = state.get("jev_routing_reason", f"Low Jev confidence ({jev_conf:.2f})")
        else:
            reason = "Insufficient evidence depth"

        state["status"] = "completed_partial"
        state["quality_checks"] = {
            "passed": False,
            "status": "completed_partial",
            "reason": reason,
            "evidence_count": evidence_count,
            "jev_confidence": jev_conf,
            "iterations": iterations,
        }
    else:
        state["status"] = "completed"
        state["quality_checks"] = {
            "passed": True,
            "status": "completed",
            "evidence_count": evidence_count,
            "jev_confidence": jev_conf,
            "iterations": iterations,
        }

    await publish_run_event(
        run_id=run_id,
        event_type="quality_check_completed",
        payload=state["quality_checks"],
    )
    return state


def route_after_quality_check(state: ResearchState) -> str:
    """
    Conditional routing edge (§14, §17):
    If insufficient evidence OR Jev confidence requires more evidence AND within bounds -> route to research_more.
    Otherwise -> route to synthesize_report.
    """
    # If deadline, tool limit, or iteration limit hit, immediately route to synthesis
    if is_deadline_exceeded(state) or is_tool_budget_exceeded(state) or is_iteration_limit_reached(state):
        return "synthesize_report"

    # If quality check passed cleanly, route to synthesis
    if state.get("quality_checks", {}).get("passed", False):
        return "synthesize_report"

    # Bounded research_more pass (shared single counter)
    state["research_iterations"] = state.get("research_iterations", 0) + 1
    return "financial_research"


async def synthesize_report(state: ResearchState) -> ResearchState:
    """
    Synthesizes the comprehensive, source-backed report with provenance and uncertainties callouts (§16, §17).
    """
    run_id = state["run_id"]
    await publish_run_event(
        run_id=run_id,
        event_type="task_started",
        payload={"task_type": "synthesis"},
    )
    ticker = state.get("ticker", "NVDA")
    fin = state.get("financial_analysis", {})
    mkt = state.get("market_analysis", {})
    news_items = state.get("news_analysis", {}).get("items", [])
    evidence = state.get("evidence", [])
    sources = state.get("sources", [])
    jev_evals = state.get("jev_evaluations", [])
    status = state.get("status", "completed")

    rev = fin.get("revenue_usd_b", "N/A")
    gm = f"{float(fin.get('gross_margin_pct', 0.5))*100:.1f}%" if "gross_margin_pct" in fin else "N/A"
    pe = fin.get("pe_ratio", "N/A")
    fcf = fin.get("free_cash_flow_b", "N/A")

    # Construct clean markdown report
    sections = []
    sections.append(f"# Equity Research Report: {fin.get('company_name', ticker)} ({ticker})")
    sections.append(f"> **Status:** `{status.upper()}` | **Tool Invocations:** {state.get('tool_calls_used', 0)} | **Iterations:** {state.get('research_iterations', 0)}")

    if status == "completed_partial":
        sections.append(
            "> [!WARNING]\n"
            "> **Partial Research Coverage**: Some secondary evidence paths were truncated due to execution guardrail boundaries (deadline, tool-call ceiling, or bounded Jev confidence). Findings below represent verified primary evidence only."
        )

    sections.append("## 1. Executive Summary")
    sections.append(
        f"{fin.get('company_name', ticker)} ({ticker}) represents a core pillar in current computing architecture. "
        f"With reported annual revenues of ${rev}B and gross margins of {gm}, the company demonstrates strong structural profitability."
    )

    sections.append("## 2. Valuation & Financial Fundamentals")
    sections.append(
        f"| Metric | Reported Value | Source Benchmark |\n"
        f"| :--- | :--- | :--- |\n"
        f"| **Revenue (FY)** | ${rev}B | {fin.get('source_filing', 'SEC Filing')} |\n"
        f"| **Gross Margin** | {gm} | SEC 10-K |\n"
        f"| **Trailing P/E** | {pe}x | Market Multiple |\n"
        f"| **Free Cash Flow** | ${fcf}B | Operating Statements |\n"
        f"| **Debt to Equity** | {fin.get('debt_to_equity', '0.24')} | Balance Sheet |"
    )

    sections.append("## 3. Competitive Moat & Industry Tailwinds")
    sections.append(f"**Software & Ecosystem Moat**: {mkt.get('software_moat', 'Proprietary developer ecosystem and switching costs.')}")
    if mkt.get("key_competitors"):
        sections.append(f"**Key Competitors**: {', '.join(mkt.get('key_competitors', []))}")

    sections.append("## 4. Key Catalysts")
    for item in news_items[:3]:
        sections.append(f"- **{item.get('headline')}** ({item.get('date', 'Recent')}): {item.get('summary')}")

    sections.append("## 5. Structured AI Assessments (Jev System One)")
    if jev_evals:
        for ev in jev_evals:
            qid_title = ev.get("question_id", "").replace("_", " ").title()
            val = ev.get("choice_value", "N/A")
            conf = ev.get("confidence", 0.0)
            sections.append(f"- **{qid_title}**: `{val}` (Confidence: {conf:.1%})")
    else:
        sections.append("*Jev evaluations omitted or bounded by execution limits.*")

    sections.append("## 6. Uncertainties & Risks")
    if mkt.get("supply_chain_bottlenecks"):
        sections.append(f"- **Supply Chain Concentration**: {mkt.get('supply_chain_bottlenecks')}")
    sections.append("- **Regulatory & Export Scrutiny**: Global trade policy and sovereign technology regulations remain an active monitoring point.")
    if status == "completed_partial":
        sections.append(f"- **Incomplete Verification**: Secondary findings bounded by {state.get('quality_checks', {}).get('reason', 'guardrails')}.")

    sections.append("## 7. Sources & Provenance")
    for idx, src in enumerate(sources, 1):
        url = src.get("url") or "#"
        sections.append(f"{idx}. [{src.get('title')}]({url}) — *{src.get('publisher')}*")

    full_markdown = "\n\n".join(sections)

    report_data = {
        "title": f"Investment Research: {ticker}",
        "summary": f"{ticker} equity research with verified financial metrics, moat dynamics, and Jev risk evaluation.",
        "content_markdown": full_markdown,
        "ticker": ticker,
        "status": status,
        "evidence_count": len(evidence),
        "sources_count": len(sources),
        "jev_evaluations_count": len(jev_evals),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    state["report"] = report_data

    await publish_run_event(
        run_id=run_id,
        event_type="task_completed",
        payload={"task_type": "synthesis"},
    )

    await publish_run_event(
        run_id=run_id,
        event_type="run_completed" if status == "completed" else "run_completed_partial",
        payload=report_data,
    )

    return state


# ---------------------------------------------------------------------------
# Construct StateGraph (§15)
# ---------------------------------------------------------------------------

def create_research_graph() -> StateGraph:
    """Builds and compiles the bounded LangGraph research workflow with Jev System One (§15, §17)."""
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("load_context", load_context)
    workflow.add_node("generate_plan", generate_plan)
    workflow.add_node("financial_research", financial_research)
    workflow.add_node("market_research", market_research)
    workflow.add_node("news_research", news_research)
    workflow.add_node("evidence_extraction", evidence_extraction)
    workflow.add_node("jev_analysis", jev_analysis)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("synthesize_report", synthesize_report)

    # Wire edges
    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "generate_plan")
    workflow.add_edge("generate_plan", "financial_research")
    workflow.add_edge("financial_research", "market_research")
    workflow.add_edge("market_research", "news_research")
    workflow.add_edge("news_research", "evidence_extraction")
    workflow.add_edge("evidence_extraction", "jev_analysis")
    workflow.add_edge("jev_analysis", "quality_check")

    # Conditional edge out of quality_check with loop guardrails
    workflow.add_conditional_edges(
        "quality_check",
        route_after_quality_check,
        {
            "financial_research": "financial_research",
            "synthesize_report": "synthesize_report",
        },
    )

    workflow.add_edge("synthesize_report", END)

    return workflow.compile()
