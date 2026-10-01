import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.profiles import FinancialProfile, FinancialProfileAssessment
from app.db.models.jev import JevEvaluation
from app.db.models.audit import AuditLog
from app.jev.client import JevClient
from app.jev.evaluators import evaluate_financial_profile
from app.domains.profiles.schemas import (
    QuestionnaireItem,
    QuestionnaireOption,
    ProfileAnswersSubmission,
    FinancialProfileResponse,
    ProfileAssessmentResponse,
    ProfileWithAssessmentResponse,
    ProfileUpdateRequest,
    JevDimensionBreakdown,
)
from app.core.logging import logger

QUESTIONNAIRE: List[QuestionnaireItem] = [
    QuestionnaireItem(
        id="investable_capital",
        title="Investable Capital",
        category="Financial Baseline",
        description="Liquid funds currently available for investment across all non-retirement and dedicated accounts.",
        why_it_matters="Determines immediate diversification capacity and portfolio sizing.",
        question_type="numeric",
        default_value=25000,
        min_value=0,
    ),
    QuestionnaireItem(
        id="monthly_contribution",
        title="Monthly Contribution",
        category="Financial Baseline",
        description="Anticipated new savings to deploy into the investment portfolio each month.",
        why_it_matters="Shapes long-term compounding trajectory and dollar-cost-averaging resilience.",
        question_type="numeric",
        default_value=500,
        min_value=0,
    ),
    QuestionnaireItem(
        id="investment_horizon",
        title="Investment Horizon",
        category="Timeframe",
        description="The anticipated duration before you will need to withdraw significant portions of invested funds.",
        why_it_matters="Longer horizons allow equity drawdowns to recover, while shorter horizons necessitate capital preservation.",
        question_type="select",
        options=[
            QuestionnaireOption(value="short", label="Short Term (< 2 Years)", description="High vulnerability to market cycle drawdowns."),
            QuestionnaireOption(value="medium", label="Medium Term (3 - 7 Years)", description="Moderate recovery time; balanced risk posture."),
            QuestionnaireOption(value="long", label="Long Term (> 7 Years)", description="High capacity to absorb multi-year equity volatility."),
        ],
    ),
    QuestionnaireItem(
        id="primary_goal",
        title="Primary Investment Objective",
        category="Objectives",
        description="The overarching financial objective for this portfolio.",
        why_it_matters="Directly drives asset allocation balance between income generation and capital appreciation.",
        question_type="select",
        options=[
            QuestionnaireOption(value="wealth_growth", label="Long-term Wealth Growth", description="Maximize compound growth over time."),
            QuestionnaireOption(value="retirement", label="Retirement Accumulation", description="Structured long-term nest egg growth."),
            QuestionnaireOption(value="capital_preservation", label="Capital Preservation", description="Protect principal against inflation and losses."),
            QuestionnaireOption(value="major_purchase", label="Major Future Purchase", description="Goal-oriented target (e.g. real estate deposit)."),
        ],
    ),
    QuestionnaireItem(
        id="experience_level",
        title="Investment Experience Level",
        category="Knowledge",
        description="Your familiarity with asset classes, market cycles, and investment mechanics.",
        why_it_matters="Calibrates the educational pacing and complexity of AI research outputs.",
        question_type="select",
        options=[
            QuestionnaireOption(value="beginner", label="Beginner", description="New to investing, index funds, and financial analysis."),
            QuestionnaireOption(value="intermediate", label="Intermediate", description="Familiar with stocks, ETFs, asset classes, and risk."),
            QuestionnaireOption(value="advanced", label="Advanced", description="Experienced with valuation multiples, financial statements, and macro."),
        ],
    ),
    QuestionnaireItem(
        id="liquidity_requirement",
        title="Liquidity Requirement",
        category="Cash Flow",
        description="How quickly and reliably you may need to convert investments into cash.",
        why_it_matters="Constrains whether funds can be committed to less liquid or volatile asset classes.",
        question_type="select",
        options=[
            QuestionnaireOption(value="immediate", label="High / Immediate", description="May need unexpected cash withdrawals within weeks."),
            QuestionnaireOption(value="moderate", label="Moderate", description="Normal predictable cash flows with scheduled withdrawals."),
            QuestionnaireOption(value="low", label="Low / Illiquid OK", description="No anticipated withdrawal needs for multiple years."),
        ],
    ),
    QuestionnaireItem(
        id="reaction_to_market_drop",
        title="Reaction to Market Drawdown",
        category="Risk Tolerance",
        description="If your portfolio drops 20% over 30 days due to market turbulence, what is your instinctive reaction?",
        why_it_matters="Identifies emotional drawdown threshold to prevent panic-selling at market bottoms.",
        question_type="select",
        options=[
            QuestionnaireOption(value="panic_sell", label="Sell to Protect Capital", description="Cut losses and preserve remaining funds in cash."),
            QuestionnaireOption(value="hold_steady", label="Hold Steady & Wait", description="Stay the course and wait for market recovery."),
            QuestionnaireOption(value="buy_more", label="Opportunistically Buy More", description="View drops as a discount and increase contributions."),
        ],
    ),
    QuestionnaireItem(
        id="emergency_fund_coverage",
        title="Emergency Cushion Coverage",
        category="Risk Capacity",
        description="How many months of essential living expenses do you hold in risk-free cash accounts?",
        why_it_matters="A robust emergency fund prevents forced selling of investment assets during financial hardships.",
        question_type="select",
        options=[
            QuestionnaireOption(value="less_than_3_months", label="Under 3 Months", description="Low buffer; unexpected costs risk liquidating investments."),
            QuestionnaireOption(value="3_to_6_months", label="3 to 6 Months", description="Standard prudent financial cushion."),
            QuestionnaireOption(value="more_than_6_months", label="Over 6 Months", description="Strong buffer allowing aggressive risk deployment."),
        ],
    ),
    QuestionnaireItem(
        id="income_stability",
        title="Income Predictability",
        category="Risk Capacity",
        description="The consistency and stability of your primary household income.",
        why_it_matters="Predictable income enables consistent dollar-cost averaging through bear markets.",
        question_type="select",
        options=[
            QuestionnaireOption(value="unstable", label="Variable / Commission / Contract", description="Income fluctuates significantly month to month."),
            QuestionnaireOption(value="moderate", label="Moderate / Salary with Variability", description="Steady baseline with periodic bonuses or shifts."),
            QuestionnaireOption(value="very_stable", label="Very Stable / Fixed Salaried", description="Highly predictable, recurring cash flow."),
        ],
    ),
]


def get_questionnaire() -> List[QuestionnaireItem]:
    return QUESTIONNAIRE


async def submit_profile_assessment(
    db: AsyncSession,
    user_id: uuid.UUID,
    answers: ProfileAnswersSubmission,
    client: JevClient,
) -> ProfileWithAssessmentResponse:
    """
    Submits questionnaire answers, runs Jev structured evaluations (§12, §13),
    applies confidence routing (§14), versions the profile, and stores assessment history.
    """
    answers_dict = answers.model_dump(mode="json")

    # Run Jev System One evaluation across risk dimensions
    jev_results, aggregate_confidence, routing_decision = await evaluate_financial_profile(
        answers_dict, client
    )

    # Extract atomic dimensions evaluated by Jev
    risk_tol_res = jev_results.get("risk_tolerance")
    risk_cap_res = jev_results.get("risk_capacity")
    liq_res = jev_results.get("liquidity_requirement")

    risk_tolerance_val = risk_tol_res.choice_value if risk_tol_res else "MODERATE"
    risk_capacity_val = risk_cap_res.choice_value if risk_cap_res else "MEDIUM"
    liquidity_val = liq_res.choice_value.lower() if liq_res and liq_res.choice_value else answers.liquidity_requirement

    # Fetch existing profile or create new one
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        profile.investable_capital = answers.investable_capital
        profile.monthly_contribution = answers.monthly_contribution
        profile.investment_horizon = answers.investment_horizon
        profile.primary_goal = answers.primary_goal
        profile.experience_level = answers.experience_level
        profile.liquidity_requirement = liquidity_val
        profile.risk_tolerance = risk_tolerance_val
        profile.risk_capacity = risk_capacity_val
        profile.profile_version += 1
    else:
        profile = FinancialProfile(
            id=uuid.uuid4(),
            user_id=user_id,
            investable_capital=answers.investable_capital,
            monthly_contribution=answers.monthly_contribution,
            investment_horizon=answers.investment_horizon,
            primary_goal=answers.primary_goal,
            experience_level=answers.experience_level,
            liquidity_requirement=liquidity_val,
            risk_tolerance=risk_tolerance_val,
            risk_capacity=risk_capacity_val,
            profile_version=1,
        )
        db.add(profile)

    await db.flush()

    # Build dimensions breakdown for assessment history
    jev_dimensions: List[JevDimensionBreakdown] = []
    dimension_names = {
        "risk_tolerance": "Psychological Risk Tolerance",
        "risk_capacity": "Financial Risk Capacity",
        "liquidity_requirement": "Liquidity Demand",
        "growth_orientation": "Growth vs Preservation Bias",
        "equity_compatibility": "Equity Allocation Compatibility",
    }

    serialized_jev_results: Dict[str, Any] = {}
    for qid, res in jev_results.items():
        dim = JevDimensionBreakdown(
            question_id=qid,
            dimension_name=dimension_names.get(qid, qid),
            judgment=res.choice_value or "UNKNOWN",
            probabilities=res.probabilities or {},
            confidence=res.confidence,
            description=f"Jev confidence-weighted categorical judgment ({res.confidence * 100:.1f}%)",
        )
        jev_dimensions.append(dim)

        serialized_jev_results[qid] = {
            "judgment": res.choice_value,
            "probabilities": res.probabilities,
            "confidence": res.confidence,
            "model_version": res.model_version,
        }

        # Persist individual Jev evaluation record (§10)
        eval_record = JevEvaluation(
            id=uuid.uuid4(),
            financial_profile_id=profile.id,
            question_id=qid,
            input_state_json=answers_dict,
            result_type=res.result_type.value,
            choice_value=res.choice_value,
            score_value=Decimal(str(res.score_value)) if res.score_value is not None else None,
            probabilities_json=res.probabilities,
            confidence=Decimal(str(res.confidence)),
            model_version=res.model_version,
        )
        db.add(eval_record)

    # Persist versioned FinancialProfileAssessment (§10)
    assessment = FinancialProfileAssessment(
        id=uuid.uuid4(),
        financial_profile_id=profile.id,
        assessment_version=profile.profile_version,
        questions_json={"total_questions": len(QUESTIONNAIRE)},
        answers_json=answers_dict,
        jev_results_json=serialized_jev_results,
        confidence=Decimal(str(aggregate_confidence)),
    )
    db.add(assessment)

    # Record security audit log (§30)
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        action="financial_profile_assessed",
        resource_type="financial_profile",
        resource_id=profile.id,
        metadata_json={
            "profile_version": profile.profile_version,
            "confidence": aggregate_confidence,
            "routing_action": routing_decision.action.value,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(profile)
    await db.refresh(assessment)

    assessment_resp = ProfileAssessmentResponse(
        id=assessment.id,
        financial_profile_id=profile.id,
        assessment_version=assessment.assessment_version,
        confidence=float(assessment.confidence),
        routing_action=routing_decision.action.value,
        routing_reason=routing_decision.reason,
        follow_up_prompt=routing_decision.follow_up_prompt,
        jev_dimensions=jev_dimensions,
        answers_summary={
            "capital": str(profile.investable_capital),
            "monthly": str(profile.monthly_contribution),
            "horizon": profile.investment_horizon,
            "goal": profile.primary_goal,
            "experience": profile.experience_level,
        },
        created_at=assessment.created_at,
    )

    return ProfileWithAssessmentResponse(
        profile=FinancialProfileResponse.model_validate(profile),
        assessment=assessment_resp,
    )


async def get_user_profile(
    db: AsyncSession,
    user_id: uuid.UUID
) -> Optional[FinancialProfileResponse]:
    """Retrieves current user's profile, enforced via user_id and PostgreSQL RLS."""
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return None
    return FinancialProfileResponse.model_validate(profile)


async def get_latest_profile_assessment(
    db: AsyncSession,
    user_id: uuid.UUID
) -> Optional[ProfileAssessmentResponse]:
    """Retrieves the most recent assessment for the user's financial profile."""
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return None

    assess_result = await db.execute(
        select(FinancialProfileAssessment)
        .where(FinancialProfileAssessment.financial_profile_id == profile.id)
        .order_by(FinancialProfileAssessment.assessment_version.desc())
        .limit(1)
    )
    assessment = assess_result.scalar_one_or_none()
    if not assessment:
        return None

    jev_dimensions: List[JevDimensionBreakdown] = []
    dimension_names = {
        "risk_tolerance": "Psychological Risk Tolerance",
        "risk_capacity": "Financial Risk Capacity",
        "liquidity_requirement": "Liquidity Demand",
        "growth_orientation": "Growth vs Preservation Bias",
        "equity_compatibility": "Equity Allocation Compatibility",
    }

    for qid, res in assessment.jev_results_json.items():
        jev_dimensions.append(
            JevDimensionBreakdown(
                question_id=qid,
                dimension_name=dimension_names.get(qid, qid),
                judgment=res.get("judgment", "UNKNOWN"),
                probabilities=res.get("probabilities", {}),
                confidence=float(res.get("confidence", 0.8)),
                description=f"Jev confidence-weighted categorical judgment ({float(res.get('confidence', 0.8)) * 100:.1f}%)",
            )
        )

    return ProfileAssessmentResponse(
        id=assessment.id,
        financial_profile_id=profile.id,
        assessment_version=assessment.assessment_version,
        confidence=float(assessment.confidence),
        routing_action="continue" if float(assessment.confidence) >= 0.80 else "gather_more_evidence",
        routing_reason=f"Recorded profile assessment version {assessment.assessment_version}",
        jev_dimensions=jev_dimensions,
        answers_summary=assessment.answers_json,
        created_at=assessment.created_at,
    )


async def update_user_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    update_data: ProfileUpdateRequest
) -> FinancialProfileResponse:
    """Updates profile attributes and increments version."""
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile does not exist. Complete questionnaire first."
        )

    for field, val in update_data.model_dump(exclude_unset=True).items():
        setattr(profile, field, val)

    profile.profile_version += 1
    await db.commit()
    await db.refresh(profile)
    return FinancialProfileResponse.model_validate(profile)
