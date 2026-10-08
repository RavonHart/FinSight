import json
import uuid
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException, status

from app.db.models.learning import LearningModule, LearningProgress, QuizAttempt
from app.db.models.profiles import FinancialProfile
from app.domains.learning.schemas import (
    QuizQuestionView,
    QuizQuestionFeedback,
    QuizAttemptResponse,
    LearningModuleSummaryResponse,
    LearningModuleDetailResponse,
    CategoryProgressItem,
    LearningSummaryResponse,
    AITutorResponse,
)
from app.jev.client import JevClient
from app.jev.evaluators import evaluate_advisory_safety
from app.jev.schemas import ConfidenceRoutingAction



def _parse_module_content(raw_content: str) -> Dict[str, Any]:
    """Parses JSON content or fallback structure from LearningModule.content."""
    try:
        data = json.loads(raw_content)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    # Fallback for plain text content
    return {
        "summary": raw_content[:200],
        "concept": raw_content,
        "example": "Review practical application in financial market history.",
        "eli5": "Think of this as foundational economic cause and effect.",
        "quant": "Standard mathematical formulas apply.",
        "visual_type": "concept_overview",
        "key_takeaways": ["Core financial literacy principle."],
        "quiz": [],
    }


async def _resolve_module(db: AsyncSession, slug_or_id: str) -> LearningModule:
    """Finds module by UUID or unique slug."""
    try:
        mod_uuid = uuid.UUID(slug_or_id)
        stmt = select(LearningModule).where(LearningModule.id == mod_uuid)
    except ValueError:
        stmt = select(LearningModule).where(LearningModule.slug == slug_or_id)

    res = await db.execute(stmt)
    module = res.scalar_one_or_none()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning module '{slug_or_id}' not found.",
        )
    return module


async def list_learning_modules(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> List[LearningModuleSummaryResponse]:
    """
    Returns list of learning modules with the current user's progress joined.
    """
    # 1. Fetch modules with optional filters
    query = select(LearningModule)
    if category:
        query = query.where(LearningModule.category.ilike(category))
    if difficulty:
        query = query.where(LearningModule.difficulty.ilike(difficulty))
    query = query.order_by(LearningModule.created_at.asc())

    mod_res = await db.execute(query)
    modules = mod_res.scalars().all()

    # 2. Fetch user's progress records
    prog_stmt = select(LearningProgress).where(LearningProgress.user_id == user_id)
    prog_res = await db.execute(prog_stmt)
    progress_map = {p.module_id: p for p in prog_res.scalars().all()}

    # 3. Assemble response
    summaries: List[LearningModuleSummaryResponse] = []
    for mod in modules:
        prog = progress_map.get(mod.id)
        content_dict = _parse_module_content(mod.content)
        summary_text = content_dict.get("summary", mod.title)

        summaries.append(
            LearningModuleSummaryResponse(
                id=mod.id,
                slug=mod.slug,
                title=mod.title,
                category=mod.category,
                difficulty=mod.difficulty,
                summary=summary_text,
                progress=prog.progress if prog else Decimal("0.00"),
                completed=prog.completed if prog else False,
                last_accessed=prog.last_accessed if prog else None,
            )
        )
    return summaries


async def get_learning_module_detail(
    db: AsyncSession,
    user_id: uuid.UUID,
    slug_or_id: str,
) -> LearningModuleDetailResponse:
    """
    Retrieves full module details, updates access progress, and calculates best/latest scores.
    """
    module = await _resolve_module(db, slug_or_id)
    content = _parse_module_content(module.content)

    # Update or insert user's progress (marking accessed)
    prog_stmt = select(LearningProgress).where(
        LearningProgress.user_id == user_id,
        LearningProgress.module_id == module.id,
    )
    prog_res = await db.execute(prog_stmt)
    prog = prog_res.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not prog:
        prog = LearningProgress(
            id=uuid.uuid4(),
            user_id=user_id,
            module_id=module.id,
            progress=Decimal("25.00"),  # Started
            completed=False,
            last_accessed=now,
        )
        db.add(prog)
    else:
        prog.last_accessed = now
        # If not completed, reading the content brings progress to at least 50%
        if not prog.completed and prog.progress < Decimal("50.00"):
            prog.progress = Decimal("50.00")

    # Fetch past quiz attempts
    attempts_stmt = (
        select(QuizAttempt)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.module_id == module.id,
        )
        .order_by(QuizAttempt.created_at.desc())
    )
    att_res = await db.execute(attempts_stmt)
    attempts = att_res.scalars().all()

    latest_score = attempts[0].score if attempts else None
    best_score = max((a.score for a in attempts), default=None) if attempts else None

    await db.commit()

    # Sanitize quiz questions so correct answer index is not leaked in the detail payload
    raw_quiz = content.get("quiz", [])
    sanitized_quiz = [
        QuizQuestionView(
            id=q.get("id", str(i)),
            question=q.get("question", ""),
            options=q.get("options", []),
        )
        for i, q in enumerate(raw_quiz)
    ]

    return LearningModuleDetailResponse(
        id=module.id,
        slug=module.slug,
        title=module.title,
        category=module.category,
        difficulty=module.difficulty,
        summary=content.get("summary", module.title),
        concept=content.get("concept", ""),
        example=content.get("example", ""),
        eli5=content.get("eli5", ""),
        quant=content.get("quant", ""),
        visual_type=content.get("visual_type", "concept_overview"),
        key_takeaways=content.get("key_takeaways", []),
        quiz_questions=sanitized_quiz,
        progress=prog.progress,
        completed=prog.completed,
        last_accessed=prog.last_accessed,
        best_score=best_score,
        latest_score=latest_score,
    )


async def submit_quiz_attempt(
    db: AsyncSession,
    user_id: uuid.UUID,
    slug_or_id: str,
    answers: Dict[str, int],
) -> QuizAttemptResponse:
    """
    Evaluates quiz submission deterministically using pure Decimal arithmetic (§3, §19, §22).
    Updates learning progress and persists the QuizAttempt record.
    """
    module = await _resolve_module(db, slug_or_id)
    content = _parse_module_content(module.content)
    raw_quiz: List[Dict[str, Any]] = content.get("quiz", [])

    if not raw_quiz:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Module '{module.slug}' does not contain an active quiz.",
        )

    correct_count = 0
    feedback_items: List[QuizQuestionFeedback] = []

    for q in raw_quiz:
        q_id = q.get("id", "")
        options = q.get("options", [])
        correct_idx = q.get("correct_index", 0)
        explanation = q.get("explanation", "")

        selected_idx = answers.get(q_id, -1)
        is_correct = selected_idx == correct_idx
        if is_correct:
            correct_count += 1

        feedback_items.append(
            QuizQuestionFeedback(
                id=q_id,
                question=q.get("question", ""),
                options=options,
                selected_index=selected_idx,
                correct_index=correct_idx,
                is_correct=is_correct,
                explanation=explanation,
            )
        )

    total_questions = len(raw_quiz)
    # Pure Decimal scoring with half-even rounding
    score = (
        Decimal(correct_count) / Decimal(total_questions) * Decimal("100.00")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    passed = score >= Decimal("70.00")

    # 1. Create durable QuizAttempt
    attempt_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    attempt = QuizAttempt(
        id=attempt_id,
        user_id=user_id,
        module_id=module.id,
        questions_json={"total": total_questions, "quiz_id": module.slug},
        answers_json=answers,
        score=score,
        created_at=now,
    )
    db.add(attempt)

    # 2. Update LearningProgress
    prog_stmt = select(LearningProgress).where(
        LearningProgress.user_id == user_id,
        LearningProgress.module_id == module.id,
    )
    prog_res = await db.execute(prog_stmt)
    prog = prog_res.scalar_one_or_none()

    if not prog:
        prog = LearningProgress(
            id=uuid.uuid4(),
            user_id=user_id,
            module_id=module.id,
            progress=Decimal("100.00") if passed else Decimal("75.00"),
            completed=passed,
            last_accessed=now,
        )
        db.add(prog)
    else:
        prog.last_accessed = now
        if passed:
            prog.completed = True
            prog.progress = Decimal("100.00")
        else:
            prog.progress = max(prog.progress, Decimal("75.00"))

    await db.commit()

    return QuizAttemptResponse(
        id=attempt_id,
        module_id=module.id,
        score=score,
        passed=passed,
        correct_count=correct_count,
        total_questions=total_questions,
        feedback=feedback_items,
        created_at=now,
    )


async def get_quiz_attempts_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    slug_or_id: str,
) -> List[QuizAttemptResponse]:
    """Retrieves full quiz attempt history for the user and module."""
    module = await _resolve_module(db, slug_or_id)
    content = _parse_module_content(module.content)
    raw_quiz_map = {q.get("id"): q for q in content.get("quiz", [])}

    stmt = (
        select(QuizAttempt)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.module_id == module.id,
        )
        .order_by(QuizAttempt.created_at.desc())
    )
    res = await db.execute(stmt)
    attempts = res.scalars().all()

    history: List[QuizAttemptResponse] = []
    for att in attempts:
        feedback_items: List[QuizQuestionFeedback] = []
        answers = att.answers_json if isinstance(att.answers_json, dict) else {}
        correct_count = 0
        total_q = len(raw_quiz_map)

        for q_id, q in raw_quiz_map.items():
            correct_idx = q.get("correct_index", 0)
            selected_idx = answers.get(q_id, -1)
            is_correct = selected_idx == correct_idx
            if is_correct:
                correct_count += 1
            feedback_items.append(
                QuizQuestionFeedback(
                    id=q_id,
                    question=q.get("question", ""),
                    options=q.get("options", []),
                    selected_index=selected_idx,
                    correct_index=correct_idx,
                    is_correct=is_correct,
                    explanation=q.get("explanation", ""),
                )
            )

        history.append(
            QuizAttemptResponse(
                id=att.id,
                module_id=module.id,
                score=att.score,
                passed=att.score >= Decimal("70.00"),
                correct_count=correct_count,
                total_questions=total_q,
                feedback=feedback_items,
                created_at=att.created_at,
            )
        )
    return history


async def get_user_learning_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> LearningSummaryResponse:
    """
    Computes overall learning metrics across curriculum (§22, §29).
    """
    # 1. All modules
    mod_stmt = select(LearningModule)
    mod_res = await db.execute(mod_stmt)
    all_modules = mod_res.scalars().all()

    # 2. User's progress
    prog_stmt = select(LearningProgress).where(LearningProgress.user_id == user_id)
    prog_res = await db.execute(prog_stmt)
    user_progress = {p.module_id: p for p in prog_res.scalars().all()}

    # 3. User's quiz scores
    quiz_stmt = select(QuizAttempt.score).where(QuizAttempt.user_id == user_id)
    quiz_res = await db.execute(quiz_stmt)
    scores = [s for (s,) in quiz_res.all()]

    total_modules = len(all_modules)
    completed_modules = sum(1 for m in all_modules if user_progress.get(m.id) and user_progress[m.id].completed)

    overall_pct = (
        (Decimal(completed_modules) / Decimal(total_modules) * Decimal("100.00")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        if total_modules > 0
        else Decimal("0.00")
    )

    avg_quiz_score = (
        (sum(scores) / Decimal(len(scores))).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        if scores
        else None
    )

    # 4. Category breakdown
    categories: Dict[str, Dict[str, Any]] = {}
    for mod in all_modules:
        cat = mod.category
        if cat not in categories:
            categories[cat] = {"total": 0, "completed": 0, "progress_sum": Decimal("0.00")}
        categories[cat]["total"] += 1
        p = user_progress.get(mod.id)
        if p:
            if p.completed:
                categories[cat]["completed"] += 1
            categories[cat]["progress_sum"] += p.progress

    cat_breakdown: Dict[str, CategoryProgressItem] = {}
    for cat, data in categories.items():
        avg_prog = (
            (data["progress_sum"] / Decimal(data["total"])).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )
            if data["total"] > 0
            else Decimal("0.00")
        )
        cat_breakdown[cat] = CategoryProgressItem(
            total_modules=data["total"],
            completed_modules=data["completed"],
            average_progress=avg_prog,
        )

    return LearningSummaryResponse(
        total_modules=total_modules,
        completed_modules=completed_modules,
        overall_completion_pct=overall_pct,
        average_quiz_score=avg_quiz_score,
        category_breakdown=cat_breakdown,
    )


# ---------------------------------------------------------------------------
# AI Tutor Guardrails (§18, §32, §69)
# ---------------------------------------------------------------------------

import re

ADVISORY_INTENT_PATTERNS = [
    re.compile(r"\bshould\s+i\s+(buy|sell|short|hold|invest\s+in|put\s+money\s+in|trade|allocate\s+to)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+much\s+(money|cash|capital)\s+should\s+i\s+(put|invest|allocate)\b", re.IGNORECASE),
    re.compile(r"\btell\s+me\s+(how\s+to|what\s+to)\s+invest\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+(stocks?|assets?|crypto|funds?|etfs?)\s+(should\s+i|to)\s+(buy|pick|choose)\b", re.IGNORECASE),
    re.compile(r"\bis\s+([A-Za-z]{1,5})\s+a\s+good\s+(buy|investment|stock|trade)\b", re.IGNORECASE),
    re.compile(r"\bguaranteed\s+(returns?|profit|gain)\b", re.IGNORECASE),
    re.compile(r"\bcan\s+you\s+(manage|trade|invest\s+for)\s+me\b", re.IGNORECASE),
]

PRESCRIPTIVE_OUTPUT_PATTERNS = [
    (re.compile(r"\byou\s+should\s+(buy|sell|invest\s+in|allocate\s+to)\b", re.IGNORECASE), "investors typically evaluate"),
    (re.compile(r"\bi\s+recommend\s+(buying|selling|purchasing|holding)\b", re.IGNORECASE), "academic financial literature analyzes"),
    (re.compile(r"\bguaranteed\s+(returns?|profits?|gains?)\b", re.IGNORECASE), "expected risk-adjusted returns"),
    (re.compile(r"\brisk-free\s+(profit|excess\s+returns?)\b", re.IGNORECASE), "theoretical baseline"),
]


def detect_advisory_intent(query: str) -> bool:
    """
    Scans user prompt for investment advice solicitation or trade recommendations (§32, §69).
    """
    for pattern in ADVISORY_INTENT_PATTERNS:
        if pattern.search(query):
            return True
    return False


def enforce_tutor_output_safety(text: str) -> str:
    """
    Scans tutor output and sanitizes any prescriptive advice phrasing into educational terms (§32).
    """
    sanitized = text
    for pattern, replacement in PRESCRIPTIVE_OUTPUT_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


async def ask_ai_tutor(
    db: AsyncSession,
    user_id: uuid.UUID,
    slug_or_id: str,
    query: str,
    mode: str = "clarify",
) -> AITutorResponse:
    """
    Interactive AI Financial Tutor grounded in module content and user's risk profile.
    Actively enforces regulatory boundary: refuses individualized investment advice (§18, §29, §32, §69).
    """
    module = await _resolve_module(db, slug_or_id)
    content = _parse_module_content(module.content)

    # Normalize mode alias (portfolio_context -> profile_context)
    normalized_mode = "profile_context" if mode in ("portfolio_context", "profile_context") else mode

    # Optional: fetch user's financial profile (macro risk posture only; NO holdings)
    prof_stmt = select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()

    profile_context_applied = False
    if profile and normalized_mode == "profile_context":
        profile_context_applied = True

    module_title = module.title
    module_category = module.category
    concept_body = content.get("concept", "")
    example_body = content.get("example", "")
    eli5_body = content.get("eli5", "")
    quant_body = content.get("quant", "")

    concepts_referenced = [module_category, module.slug.replace("-", " ").title()]

    # 1. INPUT INTENT GUARDRAIL: Multi-layer detection (§32, §69)
    # Layer 1: Fast regex / keyword heuristic (0ms cheap bypass layer)
    # Layer 2: Jev System One semantic structured judgment (catches subtle rephrasings, horizon splits, comparative advice)
    jev_client = JevClient()
    profile_summary = {
        "investment_horizon": profile.investment_horizon,
        "risk_tolerance": profile.risk_tolerance,
        "primary_goal": profile.primary_goal,
    } if profile else {}

    is_advisory_input = detect_advisory_intent(query)
    if not is_advisory_input:
        jev_input_res, jev_input_route = await evaluate_advisory_safety(
            text=query,
            context_type="input",
            client=jev_client,
            profile_data=profile_summary,
        )
        if (
            jev_input_res.choice_value == "ADVISORY_ACTIONABLE"
            or jev_input_route.action == ConfidenceRoutingAction.REFUSE_ADVISORY
        ):
            is_advisory_input = True

    if is_advisory_input:
        profile_desc = (
            f"your registered profile ({profile.investment_horizon} horizon, {profile.risk_tolerance or 'Moderate'} posture)"
            if profile
            else "your high-level investment horizon"
        )
        explanation = (
            f"### Educational Boundary & Framework Pivot (§32, §69)\n\n"
            f"**FinSight AI Tutor is an educational system and cannot provide individualized investment advice, "
            f"trade recommendations, or specific portfolio action plans.** We cannot advise you whether to buy, "
            f"sell, or allocate capital to specific assets.\n\n"
            f"**How to Analyze This Conceptually via {module_title}:**\n"
            f"Rather than seeking an actionable trade recommendation, consider the analytical principles taught in this module:\n\n"
            f"1. **Core Mechanism:** {concept_body[:220]}...\n"
            f"2. **Risk & Horizon Considerations:** Under {profile_desc}, institutional investors evaluate whether an asset's expected return adequately compensates for its return dispersion and potential drawdown, rather than attempting market timing.\n"
            f"3. **Evaluative Questions to Ask:**\n"
            f"   - Does the asset's historical correlation (ρ) provide diversification, or does it add concentrated uncompensated risk?\n"
            f"   - How does fee drag and volatility drag affect the terminal compound value of this position over your timeline?\n"
            f"   - Would an unexpected 30% drawdown jeopardize your liquidity needs?"
        )
        concepts_referenced.append("Advisory Boundary Guardrail")
        followups = [
            f"How does {module_title} mathematically model risk vs return?",
            "What is volatility drag and how does it erode compounding?",
            "Can you explain the conceptual formula without specific ticker advice?"
        ]

        disclaimer = (
            "FinSight Educational Guardrail (§32, §69): FinSight V1 is strictly a financial education "
            "and research platform. FinSight does not execute trades, manage funds, or provide individualized "
            "investment advice. Responses are generated solely to illustrate theoretical financial principles."
        )

        return AITutorResponse(
            module_slug=module.slug,
            query=query,
            mode=normalized_mode,
            explanation=explanation,
            concepts_referenced=concepts_referenced,
            suggested_followups=followups,
            profile_context_applied=profile_context_applied,
            is_advisory_refusal=True,
            disclaimer=disclaimer,
        )

    # 2. STANDARD PEDAGOGICAL MODES (Grounded in Module Curriculum)
    if normalized_mode == "eli5":
        explanation = (
            f"### Simple Analogy: {module_title}\n\n"
            f"{eli5_body}\n\n"
            f"**Connecting to your question ('{query}'):**\n"
            f"In practical terms, you don't need a Wall Street degree to apply this. Just remember that "
            f"{content.get('key_takeaways', ['consistency is key'])[0].lower()} This simple discipline protects your money over time."
        )
        concepts_referenced.append("Intuitive Analogies")
        followups = [
            f"How does {module_title} protect against inflation?",
            "Can you explain the mathematical formula behind this?",
            "What common mistake do beginner investors make with this concept?"
        ]

    elif normalized_mode == "quant":
        explanation = (
            f"### Quantitative & Mathematical Framework: {module_title}\n\n"
            f"**Analytical Model:**\n{quant_body}\n\n"
            f"**Mathematical Proof & Mechanics:**\n"
            f"When evaluating your inquiry ('{query}'), note that returns and risks follow geometric rather than simple arithmetic relations. "
            f"Specifically: {concept_body[:250]}...\n\n"
            f"**Key Equation Parameter Sensitivity:**\n"
            f"Variance directly erodes compound growth through volatility drag. Maintaining low covariance (ρ < 1.0) among holdings dampens total system variance without proportional yield loss."
        )
        concepts_referenced.extend(["Mathematical Formulation", "Quantitative Sensitivity"])
        followups = [
            "What happens if the discount rate or expected return shifts by 200 bps?",
            "How does this connect to our portfolio simulation engine?",
            "Can you give an ELI5 simple explanation instead?"
        ]

    elif normalized_mode == "profile_context":
        profile_prefix = ""
        if profile:
            profile_prefix = (
                f"Applying your registered profile dimensions (**{profile.investment_horizon}** horizon, "
                f"**{profile.primary_goal}** goal, and **{profile.risk_tolerance or 'moderate'}** risk posture):\n"
                f"*(Note: FinSight AI Tutor does not inspect individual holdings or recommend trades.)*\n\n"
            )
        else:
            profile_prefix = (
                "For a theoretical diversified growth portfolio with a 5-to-10+ year investment horizon:\n\n"
            )

        explanation = (
            f"### Financial Profile Lens: {module_title}\n\n"
            f"{profile_prefix}"
            f"When evaluating *'{query}'*, {module_title} informs long-term asset allocation and drawdown management. "
            f"{example_body}\n\n"
            f"**Pedagogical Evaluation Criteria:**\n"
            f"- Verify that targeted asset classes match your planned horizon and liquidity needs.\n"
            f"- Evaluate how volatility drag affects multi-year geometric compound returns.\n"
            f"- Rebalance systematically to capture the mathematical benefits of diversification."
        )
        concepts_referenced.extend(["Profile Alignment", "Risk Horizon"])
        followups = [
            "How can I test this in FinSight's Portfolio Simulation workspace?",
            "How does fee drag impact my long-term compounding?",
            "What quiz questions test this specific financial principle?"
        ]

    elif normalized_mode == "quiz_help":
        explanation = (
            f"### Socratic Tutor Hint: {module_title}\n\n"
            f"To answer your question regarding *'{query}'* without giving away direct quiz choices:\n\n"
            f"1. **Core Mechanism to recall:** {concept_body[:200]}...\n"
            f"2. **Think about the direction of cause and effect:** Remember how the formulas behave when time increases or when risk is magnified.\n"
            f"3. **Eliminate obvious distractors:** Any option claiming 'guaranteed 100% risk-free returns' or 'eliminating all market risk' violates the fundamental laws of finance!"
        )
        concepts_referenced.append("Socratic Guidance")
        followups = [
            "Can you explain the main concept one more time?",
            "Give me a real-world example",
            "Why is fee drag so dangerous?"
        ]

    else:  # standard "clarify"
        explanation = (
            f"### FinSight AI Tutor: {module_title}\n\n"
            f"**Core Principle:**\n{concept_body}\n\n"
            f"**Direct Answer to your question ('{query}'):**\n"
            f"In financial markets, this dynamic directly impacts long-term capital compounding. "
            f"{example_body}\n\n"
            f"**Key Rule of Thumb:**\n"
            f"{content.get('key_takeaways', ['Focus on long-term horizon and structural advantages.'])[0]}"
        )
        concepts_referenced.append("Educational Foundation")
        followups = [
            "Explain this to me like I am 5 (ELI5)",
            "What is the mathematical or quantitative formula?",
            "How does this apply to my specific investment profile?"
        ]

    # 3. OUTPUT SAFETY GUARDRAIL: Dual-layer output interception (§32, §69)
    # Layer 1: Lexical pattern sanitizer
    sanitized_explanation = enforce_tutor_output_safety(explanation)

    # Layer 2: Jev System One semantic structured output judgment
    # Catches subtle prescriptive recommendations where the LLM evaded the banned phrase list
    jev_output_res, jev_output_route = await evaluate_advisory_safety(
        text=sanitized_explanation,
        context_type="output",
        client=jev_client,
        profile_data=profile_summary,
    )

    is_advisory_output_leak = (
        jev_output_res.choice_value == "ADVISORY_ACTIONABLE"
        or jev_output_route.action == ConfidenceRoutingAction.REFUSE_ADVISORY
    )

    if is_advisory_output_leak:
        # Downstream safety interception catches the false negative before reaching user
        sanitized_explanation = (
            f"### Educational Safety Redirection (§32, §69)\n\n"
            f"The generated tutor response contained prescriptive guidance that exceeded our educational boundary. "
            f"FinSight AI Tutor does not provide actionable asset allocation directives.\n\n"
            f"**Theoretical Model Principles for {module_title}:**\n"
            f"- Academic finance evaluates asset mixes based on expected return variance and covariance (ρ), rather than prescriptive shifts.\n"
            f"- Consult a licensed fiduciary financial advisor for personalized allocation decisions."
        )
        concepts_referenced.append("Advisory Boundary Guardrail")
        is_refusal = True
    else:
        is_refusal = False

    disclaimer = (
        "FinSight Educational Disclaimer (§32): This AI Tutor response is provided exclusively for "
        "educational and informational purposes. It does not constitute individualized investment advice, "
        "financial planning recommendations, or a solicitation to buy or sell securities."
    )

    return AITutorResponse(
        module_slug=module.slug,
        query=query,
        mode=normalized_mode,
        explanation=sanitized_explanation,
        concepts_referenced=concepts_referenced,
        suggested_followups=followups,
        profile_context_applied=profile_context_applied,
        is_advisory_refusal=is_refusal,
        disclaimer=disclaimer,
    )
