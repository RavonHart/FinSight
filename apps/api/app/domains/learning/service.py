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


async def ask_ai_tutor(
    db: AsyncSession,
    user_id: uuid.UUID,
    slug_or_id: str,
    query: str,
    mode: str = "clarify",
) -> AITutorResponse:
    """
    Interactive AI Financial Tutor grounded in the module content and personalized
    with the user's risk profile and goals (§18, §29, §32).
    """
    module = await _resolve_module(db, slug_or_id)
    content = _parse_module_content(module.content)

    # Optional: fetch user's financial profile
    prof_stmt = select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()

    profile_context_applied = False
    profile_snippet = ""
    if profile:
        profile_context_applied = True
        profile_snippet = (
            f" [User Context: Experience={profile.experience_level}, "
            f"Horizon={profile.investment_horizon}, Goal={profile.primary_goal}, "
            f"Risk={profile.risk_tolerance or 'Moderate'}]"
        )

    module_title = module.title
    module_category = module.category
    concept_body = content.get("concept", "")
    example_body = content.get("example", "")
    eli5_body = content.get("eli5", "")
    quant_body = content.get("quant", "")

    # Tailored tutor response generation based on mode
    q_lower = query.lower()
    concepts_referenced = [module_category, module.slug.replace("-", " ").title()]

    if mode == "eli5":
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

    elif mode == "quant":
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

    elif mode == "portfolio_context":
        profile_prefix = ""
        if profile:
            profile_prefix = (
                f"Based on your registered profile with a **{profile.investment_horizon}** horizon, "
                f"**{profile.primary_goal}** objective, and **{profile.risk_tolerance or 'moderate'}** risk posture:\n\n"
            )
        else:
            profile_prefix = (
                "For a typical diversified growth portfolio with a 5-to-10+ year investment horizon:\n\n"
            )

        explanation = (
            f"### Portfolio Application: {module_title}\n\n"
            f"{profile_prefix}"
            f"When considering *'{query}'*, {module_title} informs your asset allocation and drawdown management. "
            f"{example_body}\n\n"
            f"**Practical Actionable Takeaway:**\n"
            f"- Verify that your active holdings match your targeted duration and liquidity needs.\n"
            f"- Avoid premature reallocation during normal market drawdowns.\n"
            f"- Rebalance systematically to capture the mathematical benefits of diversification."
        )
        concepts_referenced.extend(["Portfolio Allocation", "Risk Alignment"])
        followups = [
            "How can I test this in FinSight's Portfolio Simulation workspace?",
            "How does fee drag impact my long-term compounding?",
            "What quiz questions test this specific portfolio principle?"
        ]

    elif mode == "quiz_help":
        explanation = (
            f"### Tutor Hint for {module_title}\n\n"
            f"To answer your question regarding *'{query}'* without giving away the direct answer:\n\n"
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
            f"In financial markets, this dynamics directly impacts long-term capital compounding. "
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

    disclaimer = (
        "FinSight Educational Disclaimer (§32): This AI Tutor response is provided exclusively for "
        "educational and informational purposes. It does not constitute individualized investment advice, "
        "financial planning recommendations, or a solicitation to buy or sell securities."
    )

    return AITutorResponse(
        module_slug=module.slug,
        query=query,
        mode=mode,
        explanation=explanation,
        concepts_referenced=concepts_referenced,
        suggested_followups=followups,
        profile_context_applied=profile_context_applied,
        disclaimer=disclaimer,
    )
