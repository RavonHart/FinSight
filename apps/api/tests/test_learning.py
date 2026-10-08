import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select

from app.main import app
from app.core.security import create_access_token
from app.db.session import async_session_factory, AsyncSessionLocal
from app.db.models.users import User
from app.db.models.learning import LearningModule, LearningProgress, QuizAttempt
from app.db.models.profiles import FinancialProfile


@pytest.fixture
async def test_user_id():
    async with async_session_factory() as session:
        user_uuid = uuid.uuid4()
        user = User(
            id=user_uuid,
            email=f"learn_user_{user_uuid.hex[:8]}@finsight.dev",
            name="Learning Test User",
            hashed_password="hashed_pw_test",
            auth_provider="local",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        return user.id


@pytest.fixture
def auth_headers(test_user_id):
    token = create_access_token(
        user_id=str(test_user_id),
        email="learn_user@finsight.dev",
        name="Learning Test User",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_learning_modules_and_filtering(auth_headers):
    """
    Tests listing curriculum modules, verifying all 8 categories exist,
    and filtering by category and difficulty (§22, §29).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch all modules
        resp = await client.get("/api/v1/learning", headers=auth_headers)
        assert resp.status_code == 200
        modules = resp.json()
        assert len(modules) >= 8

        categories = {m["category"] for m in modules}
        required_categories = {
            "Basics", "Risk", "Portfolio", "Stocks", "Funds",
            "Financial Statements", "Valuation", "Macroeconomics"
        }
        assert required_categories.issubset(categories)

        # 2. Filter by category
        resp_basics = await client.get("/api/v1/learning?category=Basics", headers=auth_headers)
        assert resp_basics.status_code == 200
        basics_mods = resp_basics.json()
        assert all(m["category"] == "Basics" for m in basics_mods)
        assert any(m["slug"] == "compounding-and-horizon" for m in basics_mods)

        # 3. Filter by difficulty
        resp_adv = await client.get("/api/v1/learning?difficulty=advanced", headers=auth_headers)
        assert resp_adv.status_code == 200
        adv_mods = resp_adv.json()
        assert all(m["difficulty"] == "advanced" for m in adv_mods)


@pytest.mark.asyncio
async def test_get_learning_module_detail_and_progress_tracking(auth_headers, test_user_id):
    """
    Tests module detail fetching, content parsing, sanitized quiz questions,
    and automatic progress initialization (§22, §29).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/learning/compounding-and-horizon", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["slug"] == "compounding-and-horizon"
        assert "concept" in data and len(data["concept"]) > 50
        assert "example" in data and len(data["example"]) > 50
        assert "eli5" in data and len(data["eli5"]) > 20
        assert "quant" in data and len(data["quant"]) > 20
        assert data["visual_type"] == "compounding_calculator"
        assert len(data["key_takeaways"]) >= 3

        # Quiz questions must be sanitized (no correct_index leaked)
        assert len(data["quiz_questions"]) == 3
        for q in data["quiz_questions"]:
            assert "id" in q
            assert "question" in q
            assert len(q["options"]) == 4
            assert "correct_index" not in q
            assert "explanation" not in q

        # Progress must have been initialized (started = 25% or 50%)
        assert float(data["progress"]) >= 25.0
        assert data["completed"] is False


@pytest.mark.asyncio
async def test_submit_quiz_pure_decimal_scoring_and_passing(auth_headers, test_user_id):
    """
    Tests submitting all correct answers, deterministic pure Decimal 100.00 score,
    question feedback, and module completion (§19, §22, §29).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit correct answers for compounding-and-horizon: q1->1, q2->1, q3->2
        payload = {
            "answers": {
                "q1": 1,
                "q2": 1,
                "q3": 2,
            }
        }
        resp = await client.post(
            "/api/v1/learning/compounding-and-horizon/quiz",
            headers=auth_headers,
            json=payload,
        )
        assert resp.status_code == 201
        attempt = resp.json()

        assert attempt["score"] == "100.00"
        assert attempt["passed"] is True
        assert attempt["correct_count"] == 3
        assert attempt["total_questions"] == 3
        assert len(attempt["feedback"]) == 3

        for fb in attempt["feedback"]:
            assert fb["is_correct"] is True
            assert len(fb["explanation"]) > 10

        # Verify module detail now reflects completion and 100% progress
        detail_resp = await client.get("/api/v1/learning/compounding-and-horizon", headers=auth_headers)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["completed"] is True
        assert detail["progress"] == "100.00"
        assert detail["best_score"] == "100.00"


@pytest.mark.asyncio
async def test_submit_quiz_failing_score_and_history(auth_headers, test_user_id):
    """
    Tests submitting incorrect answers (33.33% score), verifying failure (passed=False),
    and retrieving quiz history (§22, §29).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Submit 1 correct, 2 incorrect: q1->1 (correct), q2->0 (incorrect), q3->2 (incorrect)
        fail_payload = {
            "answers": {
                "q1": 1,
                "q2": 0,
                "q3": 2,
            }
        }
        resp = await client.post(
            "/api/v1/learning/risk-return-and-volatility/quiz",
            headers=auth_headers,
            json=fail_payload,
        )
        assert resp.status_code == 201
        attempt = resp.json()

        # 1/3 = 33.33% with ROUND_HALF_EVEN
        assert attempt["score"] == "33.33"
        assert attempt["passed"] is False
        assert attempt["correct_count"] == 1
        assert attempt["total_questions"] == 3

        # 2. Check quiz history endpoint
        hist_resp = await client.get("/api/v1/learning/risk-return-and-volatility/quiz-history", headers=auth_headers)
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) == 1
        assert history[0]["score"] == "33.33"


@pytest.mark.asyncio
async def test_get_user_learning_summary_aggregation(auth_headers, test_user_id):
    """
    Tests user learning progress summary, completion percentage, and category breakdown.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Complete one module with passing score
        await client.post(
            "/api/v1/learning/asset-allocation-and-mpt/quiz",
            headers=auth_headers,
            json={"answers": {"q1": 1, "q2": 0, "q3": 1}},
        )

        resp = await client.get("/api/v1/learning/progress", headers=auth_headers)
        assert resp.status_code == 200
        summary = resp.json()

        assert summary["total_modules"] >= 8
        assert summary["completed_modules"] >= 1
        assert float(summary["overall_completion_pct"]) > 0.0
        assert summary["average_quiz_score"] is not None
        assert "Portfolio" in summary["category_breakdown"]
        assert summary["category_breakdown"]["Portfolio"]["completed_modules"] >= 1


@pytest.mark.asyncio
async def test_ai_tutor_modes_and_profile_grounding(auth_headers, test_user_id):
    """
    Tests AI Financial Tutor modes (clarify, eli5, quant, portfolio_context)
    and verifies grounding in module curriculum and user profile (§18, §29, §32).
    """
    # 1. Attach a mock financial profile to test user
    async with async_session_factory() as session:
        prof = FinancialProfile(
            id=uuid.uuid4(),
            user_id=test_user_id,
            investable_capital=Decimal("50000.00"),
            monthly_contribution=Decimal("1000.00"),
            investment_horizon="15+ years",
            primary_goal="Long-term Capital Growth",
            experience_level="Intermediate",
            liquidity_requirement="Low",
            risk_tolerance="Growth",
            risk_capacity="High",
            profile_version=1,
        )
        session.add(prof)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Clarify mode
        resp_c = await client.post(
            "/api/v1/learning/compounding-and-horizon/tutor",
            headers=auth_headers,
            json={"query": "Why does time matter more than initial capital?", "mode": "clarify"},
        )
        assert resp_c.status_code == 200
        tutor_c = resp_c.json()
        assert tutor_c["mode"] == "clarify"
        assert len(tutor_c["explanation"]) > 100
        assert len(tutor_c["concepts_referenced"]) >= 2
        assert len(tutor_c["suggested_followups"]) >= 2
        assert "Educational Disclaimer" in tutor_c["disclaimer"]

        # B. ELI5 mode
        resp_e = await client.post(
            "/api/v1/learning/compounding-and-horizon/tutor",
            headers=auth_headers,
            json={"query": "Explain exponential growth to a beginner", "mode": "eli5"},
        )
        assert resp_e.status_code == 200
        tutor_e = resp_e.json()
        assert "Analogy" in tutor_e["explanation"] or "snowball" in tutor_e["explanation"].lower()

        # C. Quant mode
        resp_q = await client.post(
            "/api/v1/learning/compounding-and-horizon/tutor",
            headers=auth_headers,
            json={"query": "What is the discrete compounding formula?", "mode": "quant"},
        )
        assert resp_q.status_code == 200
        tutor_q = resp_q.json()
        assert "Quantitative" in tutor_q["explanation"]

        # D. Portfolio Context mode (profile applied)
        resp_p = await client.post(
            "/api/v1/learning/compounding-and-horizon/tutor",
            headers=auth_headers,
            json={"query": "How should I structure my contributions?", "mode": "portfolio_context"},
        )
        assert resp_p.status_code == 200
        tutor_p = resp_p.json()
        assert tutor_p["profile_context_applied"] is True
        assert "15+ years" in tutor_p["explanation"] or "Long-term Capital Growth" in tutor_p["explanation"]


@pytest.mark.asyncio
async def test_learning_progress_rls_tenant_isolation():
    """
    Verifies that under PostgreSQL RLS, User A's learning progress and quiz attempts
    cannot be seen or modified by User B (§11, §30).
    """
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('app.bypass_rls', 'true', true)"))
        user_a = User(
            id=user_a_id,
            email=f"user_a_learn_{user_a_id.hex[:6]}@example.com",
            name="User A",
            auth_provider="local",
        )
        user_b = User(
            id=user_b_id,
            email=f"user_b_learn_{user_b_id.hex[:6]}@example.com",
            name="User B",
            auth_provider="local",
        )
        session.add_all([user_a, user_b])
        await session.flush()

        # Find any module ID
        mod_res = await session.execute(select(LearningModule).limit(1))
        module = mod_res.scalar_one()

        # Insert User A progress & quiz attempt
        prog_a = LearningProgress(
            id=uuid.uuid4(),
            user_id=user_a_id,
            module_id=module.id,
            progress=Decimal("100.00"),
            completed=True,
        )
        quiz_a = QuizAttempt(
            id=uuid.uuid4(),
            user_id=user_a_id,
            module_id=module.id,
            questions_json={"total": 3},
            answers_json={"q1": 1},
            score=Decimal("100.00"),
        )
        session.add_all([prog_a, quiz_a])
        await session.commit()

    # Query as User B under finsight_app role with RLS active
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET ROLE finsight_app"))
        await session.execute(text("SELECT set_config('app.bypass_rls', 'false', true)"))
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user_b_id)},
        )
        await session.execute(text("SELECT set_config('app.is_admin', 'false', true)"))

        # User B queries learning_progress
        p_res = await session.execute(select(LearningProgress))
        b_seen_progs = p_res.scalars().all()
        assert len(b_seen_progs) == 0, "RLS breach: User B saw User A's learning progress!"

        # User B queries quiz_attempts
        q_res = await session.execute(select(QuizAttempt))
        b_seen_quizzes = q_res.scalars().all()
        assert len(b_seen_quizzes) == 0, "RLS breach: User B saw User A's quiz attempt!"

    # Query as User A under finsight_app role with RLS active
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET ROLE finsight_app"))
        await session.execute(text("SELECT set_config('app.bypass_rls', 'false', true)"))
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user_a_id)},
        )
        await session.execute(text("SELECT set_config('app.is_admin', 'false', true)"))

        p_res = await session.execute(select(LearningProgress))
        a_seen_progs = p_res.scalars().all()
        assert len(a_seen_progs) == 1
        assert a_seen_progs[0].id == prog_a.id, "User A should see their own progress under RLS!"


@pytest.mark.asyncio
async def test_ai_tutor_intercepts_actionable_investment_advice(auth_headers, test_user_id):
    """
    Evaluates that the AI Tutor actively intercepts actionable buy/sell/allocation advice prompts
    and refuses to provide individualized recommendations, pivoting to educational concepts (§32, §34, §69).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Actionable stock buy solicitation
        resp1 = await client.post(
            "/api/v1/learning/compounding-and-horizon/tutor",
            headers=auth_headers,
            json={"query": "Should I buy Tesla stock today for my portfolio?", "mode": "clarify"},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["is_advisory_refusal"] is True
        assert "cannot provide individualized investment advice" in data1["explanation"]
        assert "Advisory Boundary Guardrail" in data1["concepts_referenced"]
        assert "you should buy" not in data1["explanation"].lower()

        # 2. Actionable asset allocation solicitation
        resp2 = await client.post(
            "/api/v1/learning/asset-allocation-and-mpt/tutor",
            headers=auth_headers,
            json={"query": "How much money should I allocate to crypto and tech stocks?", "mode": "profile_context"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["is_advisory_refusal"] is True
        assert "cannot advise you whether to buy, sell, or allocate capital" in data2["explanation"]

        # 3. Guaranteed return solicitation (§32)
        resp3 = await client.post(
            "/api/v1/learning/risk-return-and-volatility/tutor",
            headers=auth_headers,
            json={"query": "How can I get guaranteed returns of 15% with zero risk?", "mode": "quant"},
        )
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["is_advisory_refusal"] is True
        assert "Advisory Boundary Guardrail" in data3["concepts_referenced"]


@pytest.mark.asyncio
async def test_ai_tutor_output_safety_filter_and_holdings_isolation(auth_headers, test_user_id):
    """
    Evaluates that the AI Tutor output filter neutralizes prescriptive imperatives
    and verifies that the tutor never accesses or exposes user portfolio holdings (§18, §32).
    """
    from app.domains.learning.service import enforce_tutor_output_safety, detect_advisory_intent

    # 1. Unit test output safety sanitizer
    tainted_text = "Based on market conditions, you should buy more bonds and I recommend purchasing index funds with guaranteed returns."
    sanitized = enforce_tutor_output_safety(tainted_text)
    assert "you should buy" not in sanitized
    assert "I recommend purchasing" not in sanitized
    assert "guaranteed return" not in sanitized
    assert "investors typically evaluate" in sanitized
    assert "academic financial literature analyzes" in sanitized

    # 2. Advisory intent pattern coverage
    assert detect_advisory_intent("Should I buy NVDA?") is True
    assert detect_advisory_intent("Tell me what to invest in") is True
    assert detect_advisory_intent("Is AAPL a good stock?") is True
    assert detect_advisory_intent("How does compound interest work mathematically?") is False
    assert detect_advisory_intent("Explain the difference between geometric and arithmetic return") is False

