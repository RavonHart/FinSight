from typing import Dict, List, Optional
from app.jev.schemas import JevQuestionDefinition, JevResultType

# Question Registry (§13)
QUESTIONS_REGISTRY: Dict[str, JevQuestionDefinition] = {
    "risk_level": JevQuestionDefinition(
        id="risk_level",
        description="Assesses overall financial risk category based on profile attributes and stability",
        result_type=JevResultType.CHOICE,
        options=["LOW", "MODERATE", "HIGH"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "risk_tolerance": JevQuestionDefinition(
        id="risk_tolerance",
        description="Assesses behavioral and psychological willingness to absorb market drawdowns",
        result_type=JevResultType.CHOICE,
        options=["CONSERVATIVE", "MODERATE", "AGGRESSIVE"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "risk_capacity": JevQuestionDefinition(
        id="risk_capacity",
        description="Assesses objective financial ability to incur losses based on income, capital, and emergency cushion",
        result_type=JevResultType.CHOICE,
        options=["LOW", "MEDIUM", "HIGH"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "liquidity_requirement": JevQuestionDefinition(
        id="liquidity_requirement",
        description="Evaluates the degree to which capital must remain easily redeemable without penalty",
        result_type=JevResultType.CHOICE,
        options=["LOW", "MODERATE", "HIGH"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "investment_horizon": JevQuestionDefinition(
        id="investment_horizon",
        description="Evaluates structured investment time horizon horizon classification",
        result_type=JevResultType.CHOICE,
        options=["SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "growth_orientation": JevQuestionDefinition(
        id="growth_orientation",
        description="Assesses preference between capital preservation vs aggressive capital appreciation",
        result_type=JevResultType.CHOICE,
        options=["CAPITAL_PRESERVATION", "BALANCED", "GROWTH_SEEKING"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "equity_compatibility": JevQuestionDefinition(
        id="equity_compatibility",
        description="Assesses suitability for volatile equity allocations based on risk capacity and horizon",
        result_type=JevResultType.CHOICE,
        options=["LOW", "MODERATE", "HIGH"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "evidence_sufficiency": JevQuestionDefinition(
        id="evidence_sufficiency",
        description="Judges whether provided factual sources are sufficient to substantiate an empirical claim",
        result_type=JevResultType.CHOICE,
        options=["INSUFFICIENT", "SUFFICIENT", "STRONG"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
    "financial_strength": JevQuestionDefinition(
        id="financial_strength",
        description="Judges balance sheet solvency and cashflow stability",
        result_type=JevResultType.CHOICE,
        options=["WEAK", "MODERATE", "STRONG"],
        version="1.0.0",
        high_threshold=0.80,
        medium_threshold=0.50,
    ),
}


def get_question(question_id: str) -> Optional[JevQuestionDefinition]:
    return QUESTIONS_REGISTRY.get(question_id)


def list_questions() -> List[JevQuestionDefinition]:
    return list(QUESTIONS_REGISTRY.values())
