from typing import Dict, Any, Tuple
from app.jev.client import JevClient
from app.jev.schemas import JevEvaluationRequest, JevEvaluationResult, RoutingDecision
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
