from typing import Dict, Any, Tuple, Optional
from app.jev.client import JevClient
from app.jev.schemas import ConfidenceRoutingAction, JevEvaluationRequest, JevEvaluationResult, RoutingDecision
from app.jev.routing import route_confidence


async def evaluate_financial_profile(
    answers: Dict[str, Any],
    client: JevClient
) -> Tuple[Dict[str, JevEvaluationResult], float, RoutingDecision]:
    """
    Evaluates questionnaire answers using Jev System One questions (§12, §13, §14):
    - risk_tolerance
    - risk_capacity
    - liquidity_requirement
    - growth_orientation
    - equity_compatibility
    
    Computes overall confidence and executes confidence routing.
    """
    questions_to_evaluate = [
        "risk_tolerance",
        "risk_capacity",
        "liquidity_requirement",
        "growth_orientation",
        "equity_compatibility",
    ]

    requests = [
        JevEvaluationRequest(question_id=qid, input_state=answers)
        for qid in questions_to_evaluate
    ]

    results_list = await client.batch_evaluate(requests)
    results_dict: Dict[str, JevEvaluationResult] = {
        r.question_id: r for r in results_list
    }

    # Aggregate confidence reflects the weakest critical dimension if uncertain (< 0.50), else average
    confidences = [r.confidence for r in results_list]
    min_confidence = min(confidences) if confidences else 0.0
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
    aggregate_confidence = min_confidence if min_confidence < 0.50 else avg_confidence

    # Route based on confidence thresholds
    routing_decision = route_confidence(aggregate_confidence, context="profile")

    return results_dict, aggregate_confidence, routing_decision


async def evaluate_research_state(
    state: Dict[str, Any],
    client: JevClient,
) -> Tuple[Dict[str, JevEvaluationResult], float, RoutingDecision, list]:
    """
    Evaluates research state using Jev System One research questions (§13, §14):
    - evidence_sufficiency
    - financial_strength
    - growth_outlook
    - competitive_pressure
    - concentration_risk
    - risk_level

    Evaluates dynamic claim status (supported, unsupported, contested, unverified)
    using centralized thresholds configured in settings (§14).
    Computes overall confidence and executes confidence routing with context='research'.
    """
    from decimal import Decimal
    from app.core.config import settings

    fin = state.get("financial_analysis", {})
    mkt = state.get("market_analysis", {})
    evidence = state.get("evidence", [])
    sources = state.get("sources", [])
    claims = state.get("claims", [])

    # Prepare batch evaluation requests
    eval_requests = [
        JevEvaluationRequest(
            question_id="evidence_sufficiency",
            input_state={
                "evidence_count": len(evidence),
                "sources_count": len(sources),
                "is_insufficient_test": state.get("is_insufficient_test", False),
            },
        ),
        JevEvaluationRequest(
            question_id="financial_strength",
            input_state={
                "gross_margin_pct": fin.get("gross_margin_pct", 0.50),
                "free_cash_flow_b": fin.get("free_cash_flow_b", 10.0),
                "debt_to_equity": fin.get("debt_to_equity", 0.50),
            },
        ),
        JevEvaluationRequest(
            question_id="growth_outlook",
            input_state={
                "revenue_growth_yoy": fin.get("revenue_growth_yoy", 0.10),
            },
        ),
        JevEvaluationRequest(
            question_id="competitive_pressure",
            input_state={
                "software_moat": mkt.get("software_moat", ""),
                "key_competitors": mkt.get("key_competitors", []),
            },
        ),
        JevEvaluationRequest(
            question_id="concentration_risk",
            input_state={
                "supply_chain_bottlenecks": mkt.get("supply_chain_bottlenecks", ""),
            },
        ),
        JevEvaluationRequest(
            question_id="risk_level",
            input_state={"ticker": state.get("ticker", "NVDA")},
        ),
    ]

    results_list = await client.batch_evaluate(eval_requests)
    results_dict: Dict[str, JevEvaluationResult] = {r.question_id: r for r in results_list}

    # Aggregate confidence reflects minimum confidence if critical evidence sufficiency is low (< 0.50), else average
    ev_suff_res = results_dict.get("evidence_sufficiency")
    ev_suff_conf = ev_suff_res.confidence if ev_suff_res else 0.50

    confidences = [r.confidence for r in results_list]
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
    aggregate_confidence = ev_suff_conf if ev_suff_conf < settings.JEV_MEDIUM_CONFIDENCE_THRESHOLD else avg_confidence

    # Route based on confidence thresholds in research context
    routing_decision = route_confidence(aggregate_confidence, context="research")

    # Evaluate dynamic status for each claim using centralized config thresholds (§10, §14)
    supported_thresh = settings.JEV_CLAIM_SUPPORTED_THRESHOLD
    unverified_thresh = settings.JEV_CLAIM_UNVERIFIED_THRESHOLD

    updated_claims = []
    for cl in claims:
        cl_copy = dict(cl)
        # Inherit Jev evidence evaluation confidence or specific claim relevance
        rel = float(cl_copy.get("relevance_score", 0.90)) if "relevance_score" in cl_copy else aggregate_confidence

        # Determine claim status from Jev evaluation
        if cl_copy.get("is_contested"):
            cl_copy["status"] = "contested"
            cl_copy["confidence"] = Decimal(str(round(min(rel, 0.60), 3)))
        elif rel >= supported_thresh and ev_suff_conf >= settings.JEV_MEDIUM_CONFIDENCE_THRESHOLD:
            cl_copy["status"] = "supported"
            cl_copy["confidence"] = Decimal(str(round(rel, 3)))
        elif rel < unverified_thresh or ev_suff_conf < settings.JEV_MEDIUM_CONFIDENCE_THRESHOLD:
            cl_copy["status"] = "unverified"
            cl_copy["confidence"] = Decimal(str(round(min(rel, unverified_thresh - 0.05), 3)))
        else:
            cl_copy["status"] = "supported"
            cl_copy["confidence"] = Decimal(str(round(rel, 3)))

        updated_claims.append(cl_copy)

    return results_dict, aggregate_confidence, routing_decision, updated_claims


async def evaluate_advisory_safety(
    text: str,
    context_type: str,
    client: JevClient,
    profile_data: Optional[Dict[str, Any]] = None,
) -> Tuple[JevEvaluationResult, RoutingDecision]:
    """
    Evaluates learning inquiry or tutor output using Jev System One question 'advisory_intent_check' (§32, §69).
    Classifies intent as SAFE_EDUCATIONAL, AMBIGUOUS_GUIDANCE, or ADVISORY_ACTIONABLE.
    """
    request = JevEvaluationRequest(
        question_id="advisory_intent_check",
        input_state={
            "text": text,
            "context_type": context_type,  # "input" or "output"
            "profile": profile_data or {},
        },
    )
    result = await client.evaluate(request)

    if result.choice_value == "ADVISORY_ACTIONABLE":
        routing_decision = RoutingDecision(
            action=ConfidenceRoutingAction.REFUSE_ADVISORY,
            confidence=result.confidence,
            high_threshold=0.80,
            medium_threshold=0.50,
            reason=f"Semantic advisory intent detected with probability {result.probabilities.get('ADVISORY_ACTIONABLE', 0.0):.2f}; individualized advice refused (§32, §69).",
        )
    elif result.choice_value == "AMBIGUOUS_GUIDANCE":
        # §14 / §32 Safety Boundary Rule: Ambiguity defaults to the SAFE side.
        # Borderline queries are routed to refusal/framework pivot, NOT silently allowed to proceed.
        routing_decision = RoutingDecision(
            action=ConfidenceRoutingAction.REFUSE_ADVISORY,
            confidence=result.confidence,
            high_threshold=0.80,
            medium_threshold=0.50,
            reason=f"Ambiguous advisory intent detected (confidence {result.confidence:.2f}); safely refusing individualized guidance and pivoting to educational framework (§14, §32).",
        )
    else:
        routing_decision = route_confidence(result.confidence, context="advisory")

    return result, routing_decision

