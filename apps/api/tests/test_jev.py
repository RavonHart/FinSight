import pytest
from app.jev.schemas import (
    JevResultType,
    ConfidenceRoutingAction,
    JevEvaluationRequest,
    JevEvaluationResult,
)
from app.jev.questions import QUESTIONS_REGISTRY, get_question, list_questions
from app.jev.routing import route_confidence
from app.jev.client import JevClient
from app.jev.evaluators import evaluate_financial_profile


def test_jev_question_registry_integrity():
    questions = list_questions()
    assert len(questions) >= 9
    expected_qids = {
        "risk_level",
        "risk_tolerance",
        "risk_capacity",
        "liquidity_requirement",
        "investment_horizon",
        "growth_orientation",
        "equity_compatibility",
        "evidence_sufficiency",
        "financial_strength",
    }
    registered_qids = {q.id for q in questions}
    assert expected_qids.issubset(registered_qids)

    for q in questions:
        assert q.version == "1.0.0"
        assert q.high_threshold >= q.medium_threshold
        assert q.high_threshold <= 1.0
        assert q.medium_threshold >= 0.0
        assert len(q.options) > 0


def test_jev_request_response_schema_validation():
    req = JevEvaluationRequest(
        question_id="risk_tolerance",
        input_state={"reaction_to_market_drop": "panic_sell"}
    )
    assert req.question_id == "risk_tolerance"
    assert req.input_state["reaction_to_market_drop"] == "panic_sell"

    res = JevEvaluationResult(
        question_id="risk_tolerance",
        result_type=JevResultType.CHOICE,
        choice_value="CONSERVATIVE",
        score_value=None,
        probabilities={"CONSERVATIVE": 0.85, "MODERATE": 0.12, "AGGRESSIVE": 0.03},
        confidence=0.89,
        model_version="jev-v1"
    )
    assert res.choice_value == "CONSERVATIVE"
    assert res.confidence == 0.89
    assert res.result_type == JevResultType.CHOICE


def test_confidence_routing_high_confidence_path():
    # Confidence 0.85 >= High threshold 0.80
    decision = route_confidence(0.85, high_threshold=0.80, medium_threshold=0.50)
    assert decision.action == ConfidenceRoutingAction.CONTINUE
    assert decision.confidence == 0.85


def test_confidence_routing_medium_confidence_path():
    # Confidence 0.65 is between 0.50 and 0.80
    decision = route_confidence(0.65, high_threshold=0.80, medium_threshold=0.50)
    assert decision.action == ConfidenceRoutingAction.GATHER_MORE_EVIDENCE
    assert decision.confidence == 0.65


def test_confidence_routing_low_confidence_profile_clarification():
    # Confidence 0.38 < Medium threshold 0.50 in profile context
    decision = route_confidence(0.38, context="profile", high_threshold=0.80, medium_threshold=0.50)
    assert decision.action == ConfidenceRoutingAction.REQUEST_CLARIFICATION
    assert decision.follow_up_prompt is not None


def test_confidence_routing_low_confidence_research_insufficient():
    # Confidence 0.38 < Medium threshold 0.50 in research context (§14)
    decision = route_confidence(0.38, context="research", high_threshold=0.80, medium_threshold=0.50)
    assert decision.action == ConfidenceRoutingAction.MARK_INSUFFICIENT
    assert decision.confidence == 0.38


@pytest.mark.asyncio
async def test_jev_client_calibrated_evaluation():
    client = JevClient()

    # Conservative inputs
    answers_conservative = {
        "reaction_to_market_drop": "panic_sell",
        "emergency_fund_coverage": "less_than_3_months",
        "income_stability": "unstable",
        "investment_horizon": "short",
        "primary_goal": "capital_preservation",
        "liquidity_requirement": "immediate",
    }
    results, confidence, routing = await evaluate_financial_profile(answers_conservative, client)
    assert len(results) == 5
    assert results["risk_tolerance"].choice_value == "CONSERVATIVE"
    assert results["risk_capacity"].choice_value == "LOW"
    assert results["growth_orientation"].choice_value == "CAPITAL_PRESERVATION"
    assert confidence >= 0.80
    assert routing.action == ConfidenceRoutingAction.CONTINUE

    # Aggressive / high-growth inputs
    answers_aggressive = {
        "reaction_to_market_drop": "buy_more",
        "emergency_fund_coverage": "more_than_6_months",
        "income_stability": "very_stable",
        "investment_horizon": "long",
        "primary_goal": "wealth_growth",
        "liquidity_requirement": "low",
    }
    results_agg, confidence_agg, routing_agg = await evaluate_financial_profile(answers_aggressive, client)
    assert results_agg["risk_tolerance"].choice_value == "AGGRESSIVE"
    assert results_agg["risk_capacity"].choice_value == "HIGH"
    assert results_agg["equity_compatibility"].choice_value == "HIGH"
    assert confidence_agg >= 0.80
    assert routing_agg.action == ConfidenceRoutingAction.CONTINUE


@pytest.mark.asyncio
async def test_jev_client_timeout_and_fallback_resilience():
    # Point client to an invalid URL to test network failure resilience and fallback
    client = JevClient(api_key="real-test-key", base_url="http://invalid.nonexistent.domain", timeout_seconds=0.5)
    req = JevEvaluationRequest(
        question_id="risk_tolerance",
        input_state={"reaction_to_market_drop": "panic_sell"}
    )
    result = await client.evaluate(req)
    assert result.question_id == "risk_tolerance"
    assert result.choice_value == "CONSERVATIVE"
    assert result.confidence > 0.0
