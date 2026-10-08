# FinSight — Project Status & Handover Documentation

**Last Updated:** October 8, 2026  
**Current Phase Completed:** Phase 9 (Watchlists & Automated Market Scans — Idempotency & Aggregated Fan-out Hardened)  
**Next Phase Ready:** Phase 10 (Production Hardening, Performance Optimization & Launch)  
**Test Suite:** 72/72 Tests Passing (100% Green)  
**Git Head Commit:** `9466a78`  

---

## 1. Executive Summary

FinSight is an institutional-grade, AI-assisted financial research, portfolio analytics, and investment learning platform. It enforces deterministic arithmetic (pure `Decimal` calculations), hard loop termination guardrails, strict tenant isolation via PostgreSQL Row-Level Security (RLS), and Jev "System One" calibrated confidence routing.

The project currently has **Phases 1 through 9 fully implemented, unit/integration tested, and browser-verified** within Docker containers.

```
+---------------------------------------------------------------------------------------+
|                                    FINSIGHT PLATFORM                                  |
+--------------------------+----------------------------+-------------------------------+
|   Phase 1: Foundation    |  Phase 2: Profiles & Goals |  Phase 3: Financial Engine    |
|   - Docker Compose       |  - 7 Risk Dimensions       |  - Pure Decimal Math          |
|   - Postgres + pgvector  |  - Jev Confidence Routing  |  - Bounded XIRR + Fallback    |
|   - Redis + Celery       |  - Versioned Profiles      |  - Holdings Sync & Valuation  |
|   - JWT Auth & RLS       |  - Financial Goals CRUD    |  - Idempotent Transactions    |
+--------------------------+----------------------------+-------------------------------+
|   Phase 4: Research      |  Phase 5: Jev Evaluations  |  Phase 6: Research Workspace  |
|   - LangGraph Workflow   |  - System One Fast Screen  |  - 3-Panel Provenance UI      |
|   - Mid-Flight Deadlines |  - Centralized Thresholds  |  - Replay-Then-Subscribe SSE  |
|   - Evidence Vector DB   |  - Single-Iteration Bounded|  - Stable Citation Indices    |
|   - Tool Budget Ceilings |  - Durable Claim Scans     |  - Dynamic Stepper & Drawer   |
+--------------------------+----------------------------+-------------------------------+
|   Phase 7: Simulation Engine & Interactive UX                                         |
|   - Pure Decimal Closed-Form Monthly Compounding (Zero Solver Required)               |
|   - Honest 3-Trajectory Visualizer (Bear / Base / Bull, No Misleading Fan Shading)    |
|   - Mandatory Regulatory Model Disclosure (§20, §32)                                  |
|   - Dynamic Portfolio Seeding & Pinned engine_version="financial-engine-v1"           |
+---------------------------------------------------------------------------------------+
|   Phase 8: Interactive Learning & AI Tutor (Jev-Hardened)                             |
|   - 8 Curated Curriculum Categories (Basics, Risk, Portfolio, Stocks, Funds, etc.)   |
|   - Multi-Lens Explanation Switching (Core Concept / ELI5 Analogy / Quant Rigor)     |
|   - Interactive In-Lesson Concept Sandbox & Fee Drag Slider Simulator                 |
|   - Grounded AI Financial Tutor with User Risk Profile Personalization (§18, §32)    |
|   - Multi-Layer Jev Advisory Semantic Guardrail (advisory_intent_check, §32, §69)    |
|   - Structural Dependency Injection Isolation (No Portfolio/Holdings Access)         |
|   - Downstream Semantic Output Interception for Prescriptive Advice Leaks             |
|   - Deterministic Decimal Quiz Grading with Pedagogical Feedback & RLS Isolation      |
+---------------------------------------------------------------------------------------+
|   Phase 9: Watchlists & Automated Market Scans (Idempotent & Aggregated Fan-out)      |
|   - Watchlists & Tracked Items CRUD with PostgreSQL Row-Level Security (RLS)          |
|   - Deterministic Signal Analysis (Momentum Shifts, Valuation Compression, Drawdowns) |
|   - Celery Beat Daily Scheduled Scans with Date-Unique Idempotency Keys (§38, §52)    |
|   - In-Flight Concurrency Locks Preventing Duplicate Concurrent Scan Runs             |
|   - Single Aggregated Notification Fan-out (No Notification Bell Flooding)            |
|   - Glassmorphic Next.js Watchlists Workspace with Live Scan Execution & Drawer       |
+---------------------------------------------------------------------------------------+
```

---

## 2. Phase-by-Phase Completion Status

### Phase 1: Architecture & Foundation
- **Dockerized Multi-Container Topology**: `postgres:16` (pgvector enabled), `redis:7-alpine`, FastAPI `api`, Celery `worker`, Celery `beat`, and Next.js 14 `web`.
- **Database Schema**: 26 tables migrated, with PostgreSQL Row-Level Security (`rls_policies.sql`) guaranteeing multi-tenant isolation at the database level.
- **Authentication**: JWT access + refresh tokens, bcrypt password hashing, session management, and tenant isolation tests.

### Phase 2: Financial Profiles & Goals
- **Risk Assessment Questionnaire**: 7 dimensions (horizon, goal, experience, liquidity, market reaction, emergency fund, income stability).
- **Jev Calibration**: Automatic scoring into conservative, moderate, growth, or aggressive tiers with confidence evaluation and ambiguity clarification routing.
- **Financial Goals**: Versioned target dates, target amounts, priority ranking, and goal progress tracking.

### Phase 3: Deterministic Financial Engine
- **Pure-Decimal Arithmetic**: Exact currency and ratio calculations using `ROUND_HALF_EVEN`.
- **Valuation & P&L**: Unweighted cost basis, market valuation, unrealized/realized gains.
- **CAGR, Drawdown, Inflation Discounting**: Bounded mathematical functions with negative value defense.
- **XIRR**: Newton-Raphson solver bounded to 100 iterations with fallback to annualized return on non-convergence.
- **Holdings Sync**: Atomic transaction updates to portfolio positions.

### Phase 4: Autonomous Research Engine
- **LangGraph Multi-Agent Architecture**: Planner -> Tool Executor -> Evidence Aggregator -> Jev Evaluator -> Synthesis.
- **Hard Runtime Ceilings**: Max 15 tool calls, 4-minute execution timeout.
- **Deterministic Deduplication**: Content hashing prevents duplicate evidence gathering.
- **Vector Storage**: Chunking and embedding persistence in pgvector.

### Phase 5: Jev System One Research Layer
- **Calibrated Evaluations**: High/Medium/Low thresholds across risk, capacity, financial strength, and evidence sufficiency.
- **Single Iteration Cap**: Prevents infinite research loops on ambiguous states.
- **Durable Claim Scans**: Evaluates individual factual claims against extracted evidence.

### Phase 6: Research Workspace UX
- **Three-Panel UI**: Query formulation -> Live progress stepper -> Dual-mode synthesis & evidence viewer.
- **Replay-Then-Subscribe SSE**: Zero dropped events on mid-run page reloads.
- **Stable Citation Indices**: Fixed citation markers link directly to verified sources in drawer.

### Phase 7: Simulation Engine & Interactive Projections UX
- **Pure-Decimal Closed-Form Compounding**:
  - Step-by-step monthly compounding: $B_t = B_{t-1}(1 + r_{\text{net}}) + C_t - W_t$.
  - Models user contributions, fee drag, optional decumulation/withdrawals, and real purchasing power discounting via `calculate_inflation_adjusted_value`.
  - Zero numerical approximation or solver required.
- **Honest Multi-Scenario Visualizer (§20, §32)**:
  - 3 distinct deterministic trajectories: Bear (Base - 3% return, Base + 1.5% inflation), Base, and Bull (Base + 3% return, Base - 0.5% inflation).
  - Clean SVG line chart with distinct solid strokes (Rose, Emerald, Indigo) and **zero misleading shaded confidence bands or Monte Carlo probability fans**.
  - Interactive scrub column showing exact point-in-time deterministic dollar values on hover.
- **Mandatory Regulatory Banner**: Explicit model disclosure informing users that projections are mathematical illustrations, not guarantees or probability distributions.
- **Reproducibility**: Runs pinned with `engine_version="financial-engine-v1"` and persisted to `simulation_runs`.
- **Dynamic Portfolio Seeding**: Instant capital seeding from the user's active portfolio holdings.

### Phase 8: Interactive Learning & AI Tutor
- **8 Core Curriculum Domains (§29)**:
  - *Basics*: The Compounding Machine & Time Horizon
  - *Risk*: Risk vs. Return & Geometric Volatility Drag
  - *Portfolio*: Modern Portfolio Theory & Uncorrelated Assets
  - *Stocks*: Equity Ownership & Fundamental Drivers of Stock Value
  - *Funds*: Index Funds vs. Active ETFs & Fee Drag Mechanics
  - *Financial Statements*: Three-Statement Analysis: Income, Balance Sheet & Cash Flow
  - *Valuation*: Intrinsic Value: DCF vs. Price Multiples
  - *Macroeconomics*: Central Banks, Interest Rates & Macroeconomic Cycles
- **Multi-Lens Pedagogical Explanations**:
  - Instant lens switcher on every lesson: Core Concept, ELI5 / Analogy, Quantitative Rigor.
- **Embedded Interactive Concept Sandbox**:
  - Real-time parameter sliders computing exact terminal balances, gross vs. net capital, and fee drag loss in real-time.
- **Interactive AI Financial Tutor (§18, §29, §32, §69)**:
  - Grounded directly in lesson curriculum and registered financial profile.
  - Multi-layer defense architecture:
    1. Layer 1: Fast regex / keyword heuristic (0ms rejection of obvious compliance triggers).
    2. Layer 2: **Jev System One Structured Semantic Judgment** (`advisory_intent_check`):
       - Detects subtle rephrasings (e.g. personal capital/horizon asset-split solicitations, comparative profile instructions, covert multi-turn solicitations).
       - Outputs calibrated probabilities and routes via `ConfidenceRoutingAction.REFUSE_ADVISORY`.
    3. Layer 3: **Structural Dependency Injection Boundary**:
       - The tutor service only injects `FinancialProfile` (macro horizon, experience, goal, risk posture).
       - It is structurally barred from reading `holdings` or `portfolios`, guaranteeing it can never give holding-specific advice.
    4. Layer 4: **Lexical Output Sanitizer**: Neutralizes prescriptive verbs.
    5. Layer 5: **Downstream Jev Semantic Output Interception**:
       - If generated LLM text leaks prescriptive advice without banned keywords (e.g. *"a sensible next step given your horizon would be increasing your equity allocation"*), Jev output classification intercepts it downstream before reaching the client, replacing the payload with a regulatory redirection framework and `is_advisory_refusal = True`.
- **Deterministic Quiz Grading & Progress Tracking**:
  - Sanitized question views (zero correct answer index leakage).
  - Pure `Decimal` score computation with `ROUND_HALF_EVEN`.
  - Passing threshold (≥ 70%) marks module complete and updates dashboard mastery rate.
  - PostgreSQL Row-Level Security (`learning_progress_isolation_policy`, `quiz_attempts_isolation_policy`) guarantees multi-tenant isolation.

#### Residual Risk & Boundary Disclosure (§32, §69)
- **Semantic Boundary vs. Formal Proof**: The multi-layer defense (lexical heuristics + Jev System One semantic structured judgment + downstream output interception) is *meaningfully harder to evade* than regex matching, but does not constitute a mathematically impenetrable boundary.
- **LLM-Judging-LLM Residual Failure Modes**: Because Jev operates as an LLM-backed structured evaluator, it inherits model calibration drift and novel phrasing evasion risks.
- **Structural DI as Ground Truth**: The primary non-negotiable safeguard is the architectural Dependency Injection boundary: the tutor service is physically isolated from the `Portfolio` and `Holding` tables. The tutor has access only to high-level profile macro dimensions (`FinancialProfile`), meaning it structurally cannot provide holding-specific buy/sell directives regardless of model behavior.
- **Cost Ceilings & Resource Controls (§31, §46)**: Redis-backed hourly interaction quotas (`TUTOR_HOURLY_RATE_LIMIT = 60`) govern `/tutor` endpoints to prevent unbounded token and Jev evaluation consumption from looped interactions.

### Phase 9: Watchlists & Automated Market Scans
- **Database Schema & RLS Isolation (`0004_watchlists_rls.py`)**:
  - `watchlists`, `watchlist_items`, `watchlist_scans`, and `notifications` tables.
  - Added unique index on `watchlist_scans.idempotency_key`.
  - Enabled and forced PostgreSQL Row-Level Security on `watchlist_items` and `watchlist_scans` with tenant isolation policies checking `watchlists.user_id = current_user_id`.
- **Scan Idempotency & Concurrency Defenses (§38, §52)**:
  - Daily Celery beat scheduled runs use date-deterministic idempotency keys: `scheduled_scan:{watchlist_id}:{YYYY-MM-DD}`.
  - In-flight concurrency lock: If a scan is currently `queued` or `running` for a watchlist, subsequent triggers are skipped with 409 Conflict / existing scan returned.
  - Unique DB index constraint prevents race conditions from creating duplicate scan records.
- **Aggregated Notification Fan-out Architecture (§38, §52)**:
  - Bounded notification creation: A scan produces **exactly ONE aggregated notification** summarizing all detected signals (e.g., *"Watchlist Scan: 3 signals in 'Tech Leaders'"* with bullet points) rather than spamming one notification per finding.
  - Supports user-driven mark-read operations for individual or bulk notifications.
- **Signal Detection & Analysis Engine**:
  - Deterministic evaluation of price changes and volatility against configured thresholds:
    - `momentum_shift`: 20-day return momentum trend.
    - `valuation_compression`: Pullbacks and value territory entries.
    - `drawdown_alert`: Severe price drops exceeding risk thresholds.
  - Typed findings persisted as JSONB in `watchlist_scans.findings` with severity (`high`, `medium`, `low`).
- **Celery Beat Background Tasks**:
  - `scheduled_watchlist_scan`: Iterates all active scan-enabled watchlists on daily schedule with date idempotency.
  - `refresh_holding_prices`: Periodic batch refresher updating market valuations across active holdings.
  - `NullPool` database connection architecture ensuring event-loop safety across threaded worker executions.
- **Watchlists & Notifications Workspace UX**:
  - Glassmorphic Next.js interface at `/app/watchlists`.
  - Watchlist selector, creation modal, and item management (instant ticker lookup & removal).
  - Manual "Run Market Scan" button with live loading state.
  - Findings cards with color-coded severity badges (Emerald/Amber/Rose) and metric tags.
  - Notification drawer with unread count badge and bulk "Mark all read" capability.
  - Connected from the main Dashboard.

---

## 3. Git Commit History

| Commit | Description |
|:-------|:------------|
| *(Pending)* | **feat: Phase 9 — Watchlists & Automated Market Scans with Idempotency, Aggregated Notifications, Celery Tasks & RLS** |
| `61742be` | feat: Phase 8 — AI Tutor Jev semantic guardrail with safe default routing, hourly cost ceilings, and residual-risk documentation |
| `31c26b5` | feat: Phase 8 — Interactive Learning & AI Tutor with Curriculum, Sandbox & Quiz Grading |
| `ae0bfe6` | feat: Phase 7 — Deterministic Simulation Engine & Interactive Projections UX |
| `6cb21ed` | fix: resolve research UI stuck step, link pgvector chunk storage to evidence, and bind stable citation indexing |
| `ead493a` | feat: Phase 6 — Research UX & Three-Panel Workspace with live SSE streaming |
| `1cf452f` | feat: Phase 5 — Jev Research Layer with calibrated confidence routing and claim verification |
| `5622080` | feat: Phase 4 — LangGraph Research Engine with budget ceilings and evidence extraction |
| `bc92556` | feat: Phase 3 — Deterministic Financial Engine with Decimal math, XIRR, and holdings sync |
| `8a7a0b5` | feat: Phase 2 — Financial Profile assessment, versioning, and goals CRUD |
| `e8e1927` | feat: Phase 1 — Project foundation, Docker setup, RLS migrations, and Auth |

---

## 4. Test Suite Health (72/72 Passing)

All unit and integration tests run in the containerized environment against live PostgreSQL and Redis instances:

```bash
docker compose exec -T api pytest tests/ -v
```

```
tests/test_auth.py (3 passed)
tests/test_celery.py (2 passed)
tests/test_financial_engine.py (9 passed)
tests/test_health.py (3 passed)
tests/test_jev.py (7 passed)
tests/test_learning.py (11 passed)
tests/test_models.py (1 passed)
tests/test_portfolios.py (4 passed)
tests/test_profiles_and_goals.py (6 passed)
tests/test_research.py (12 passed)
tests/test_rls.py (1 passed)
tests/test_simulations.py (6 passed)
tests/test_watchlists.py (6 passed)
============================== 72 passed in ~8.7s ==============================
```

---

## 5. Directory Structure & Key Files

```
d:/FinSight/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── agents/            # LangGraph workflow, research graph & supervisor
│   │   │   ├── api/router.py      # Master API router mounting all domain routers
│   │   │   ├── core/              # Config, security, JWT, database session
│   │   │   ├── db/
│   │   │   │   ├── migrations/    # Alembic migrations (0001, 0002, 0003_learning_rls_and_seed)
│   │   │   │   └── models/        # SQLAlchemy 2.0 async models (26 tables)
│   │   │   ├── domains/
│   │   │   │   ├── auth/          # Auth endpoints & service
│   │   │   │   ├── jev/           # Jev calibrated confidence evaluator
│   │   │   │   ├── learning/      # Learning domain router, service, schemas, AI tutor
│   │   │   │   ├── portfolios/    # Portfolios, holdings, transactions
│   │   │   │   ├── profiles/      # Financial profiles & risk scoring
│   │   │   │   ├── research/      # Research projects, runs, evidence, sources
│   │   │   │   └── simulations/   # Simulation domain router, service, schemas
│   │   │   └── finance/
│   │   │       ├── engine.py      # Decimal valuation, XIRR, inflation discounting
│   │   │       └── simulation.py  # Compound growth & multi-scenario simulation engine
│   │   └── tests/                 # 62 async pytest test cases
│   └── web/
│       ├── app/
│       │   ├── app/
│       │   │   ├── dashboard/     # Workspace hub with active module links
│       │   │   ├── learning/      # Learning Hub (/app/learning) & Lesson Workspace (/[slug])
│       │   │   ├── portfolio/     # Portfolio management & analytics UI
│       │   │   ├── profile/       # Financial questionnaire & goals UI
│       │   │   ├── research/      # Three-panel research workspace & SSE stream
│       │   │   └── simulation/    # Phase 7 simulation workspace & SVG visualizer
│       │   ├── login/             # User sign-in
│       │   └── signup/            # User registration
│       ├── components/
│       │   ├── auth-context.tsx   # React Auth context & token persistence
│       │   ├── evidence-provenance-panel.tsx # Right drawer for evidence & citations
│       │   ├── markdown-report.tsx           # Report renderer with clickable citations
│       │   └── research-plan-panel.tsx       # Left drawer with execution stepper & Jev
│       └── lib/
│           ├── auth.ts            # Auth client & token management
│           ├── learning.ts        # Phase 8 Learning API & AI Tutor client
│           ├── portfolio.ts       # Portfolio API client
│           ├── profile.ts         # Profile & goals API client
│           ├── research.ts        # Research API & SSE client
│           └── simulation.ts      # Phase 7 simulation API client
├── docker-compose.yml             # Orchestration for postgres, redis, api, worker, beat, web
└── PROJECT_STATUS_HANDOVER.md     # This document
```

---

## 6. How to Resume & Run Locally

### Start Containers
```bash
docker compose up -d
```

### Run Backend Tests
```bash
docker compose exec -T api pytest tests/ -v
```

### Apply Web Changes (if modifying frontend)
```bash
docker compose build web
docker compose up -d web
```

### Access Platform in Browser
- **Frontend App**: `http://localhost:3000` (Dashboard: `http://localhost:3000/app/dashboard`)
- **Learning Hub**: `http://localhost:3000/app/learning`
- **Research Workspace**: `http://localhost:3000/app/research`
- **Simulation Workspace**: `http://localhost:3000/app/simulation`
- **Backend API Docs (Swagger)**: `http://localhost:8000/docs`
- **Test Credentials**: `demo@finsight.dev` / `DemoPass123!`

---

## 7. Roadmap: Next Up — Phase 10 (Production Hardening, Observability & Launch)

According to the product blueprint (§38, §52, §70), Phase 10 introduces:
1. **Production Observability & Metrics**: Prometheus / OpenTelemetry instrumentation for Celery task throughput, Jev judgment latencies, and financial engine execution times.
2. **End-to-End Synthetic Verification**: Full scenario suites validating research-to-portfolio workflows under high concurrency.
3. **Audit Log Export & Regulatory Packager**: PDF / JSON compliance report generation bundling citations, Jev confidence trails, and pure-decimal simulation parameters.
4. **Final Security & Rate Limit Tuning**: Fine-tuning Redis tiered burst and sustained token-bucket windows for institutional deployment.
