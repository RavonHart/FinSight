# FinSight — Project Status & Handover Documentation

**Last Updated:** October 2, 2026  
**Current Phase Completed:** Phase 7 (Deterministic Simulation Engine & Interactive Projections UX)  
**Next Phase Ready:** Phase 8 (Interactive Learning & AI Tutor)  
**Test Suite:** 55/55 Tests Passing (100% Green)  
**Git Head Commit:** `ae0bfe6`  

---

## 1. Executive Summary

FinSight is an institutional-grade, AI-assisted financial research, portfolio analytics, and investment learning platform. It enforces deterministic arithmetic (pure `Decimal` calculations), hard loop termination guardrails, strict tenant isolation via PostgreSQL Row-Level Security (RLS), and Jev "System One" calibrated confidence routing.

The project currently has **Phases 1 through 7 fully implemented, unit/integration tested, and browser-verified** within Docker containers.

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
- **Pure `Decimal` Arithmetic**: All portfolio valuation, allocation weights, sector exposures, CAGR, and HHI calculations use strict `Decimal` precision with half-even rounding (`ROUND_HALF_EVEN`). Zero binary float representation leakage.
- **Bounded-Iteration XIRR with Newton-Raphson Fallback**: Handles non-converging cash flows gracefully without infinite loops or runtime crashes.
- **Transaction Idempotency**: Unique constraint checks and idempotency keys prevent duplicate transaction insertion under race conditions.

### Phase 4: Autonomous Research Graph (LangGraph)
- **Multi-Agent Orchestration**: Research supervisor coordinating financial analysis, market analysis, news synthesis, evidence validation, and report synthesis.
- **Hard Runtime Budgets & Mid-Execution Deadlines**:
  - `MAX_RESEARCH_ITERATIONS = 3`
  - `MAX_TOOL_CALLS = 12`
  - `RUN_TIMEOUT_SECONDS = 300` propagated directly into tool-level `effective_timeout`, preventing slow external providers from hanging worker threads.
- **Pgvector Evidence Chunks**: Evidence paragraphs stored as pgvector `DocumentChunk` records for semantic retrieval.

### Phase 5: Jev Research Layer
- **System One Calibrated Screen**: Dual-speed architecture evaluating claim validity, factual consistency, and confidence scores.
- **Centralized Threshold Configuration**: Unified in `JevThresholdConfig`:
  - `JEV_HIGH_CONFIDENCE_THRESHOLD = 0.80` (Direct synthesis)
  - `JEV_MEDIUM_CONFIDENCE_THRESHOLD = 0.50` (Bounded single retry)
  - `< 0.50` (Flagged as unverified/insufficient)
- **Bounded Single-Iteration Cap**: Jev low confidence can trigger at most one targeted gap-fill query within the research run's lifetime budget.

### Phase 6: Research Workspace & Three-Panel UX
- **Three-Panel Layout**:
  - Left Panel: Run overview, live execution stepper, Jev confidence judgments, and claim status tags with explicit numerical thresholds (`Supported Jev ≥ 0.80`).
  - Middle Panel: Synthesized Markdown report with interactive superscript citation tags (`[1]`, `[2]`).
  - Right Panel: Evidence Drawer with Trust Tier Badges (Tier 1 Regulatory, Tier 2 Institutional, Tier 3 Web) and persistent database-backed `citation_index`.
- **Replay-Then-Subscribe SSE Architecture**: Clients connecting or reconnecting mid-run receive a complete historical snapshot frame before live streaming events attach, eliminating race conditions and missed progress frames.

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

---

## 3. Git Commit History

| Commit | Description |
|:-------|:------------|
| `ae0bfe6` | **feat: Phase 7 — Deterministic Simulation Engine & Interactive Projections UX** |
| `6cb21ed` | fix: resolve research UI stuck step, link pgvector chunk storage to evidence, and bind stable citation indexing |
| `ead493a` | feat: Phase 6 — Research UX & Three-Panel Workspace with live SSE streaming |
| `1cf452f` | feat: Phase 5 — Jev Research Layer with calibrated confidence routing and claim verification |
| `5622080` | feat: Phase 4 — LangGraph Research Engine with budget ceilings and evidence extraction |
| `bc92556` | feat: Phase 3 — Deterministic Financial Engine with Decimal math, XIRR, and holdings sync |
| `8a7a0b5` | feat: Phase 2 — Financial Profile assessment, versioning, and goals CRUD |
| `e8e1927` | feat: Phase 1 — Project foundation, Docker setup, RLS migrations, and Auth |

---

## 4. Test Suite Health (55/55 Passing)

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
tests/test_models.py (1 passed)
tests/test_portfolios.py (4 passed)
tests/test_profiles_and_goals.py (6 passed)
tests/test_research.py (12 passed)
tests/test_rls.py (1 passed)
tests/test_simulations.py (6 passed)
============================== 55 passed in ~6.0s ==============================
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
│   │   │   ├── db/models/         # SQLAlchemy 2.0 async models (26 tables)
│   │   │   ├── domains/
│   │   │   │   ├── auth/          # Auth endpoints & service
│   │   │   │   ├── jev/           # Jev calibrated confidence evaluator
│   │   │   │   ├── portfolios/    # Portfolios, holdings, transactions
│   │   │   │   ├── profiles/      # Financial profiles & risk scoring
│   │   │   │   ├── research/      # Research projects, runs, evidence, sources
│   │   │   │   └── simulations/   # Simulation domain router, service, schemas
│   │   │   └── finance/
│   │   │       ├── engine.py      # Decimal valuation, XIRR, inflation discounting
│   │   │       └── simulation.py  # Compound growth & multi-scenario simulation engine
│   │   └── tests/                 # 55 async pytest test cases
│   └── web/
│       ├── app/
│       │   ├── app/
│       │   │   ├── dashboard/     # Workspace hub with active module links
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
- **Research Workspace**: `http://localhost:3000/app/research`
- **Simulation Workspace**: `http://localhost:3000/app/simulation`
- **Backend API Docs (Swagger)**: `http://localhost:8000/docs`
- **Test Credentials**: `demo@finsight.dev` / `DemoPass123!`

---

## 7. Roadmap: Next Up — Phase 8 (Interactive Learning & AI Tutor)

According to the product blueprint, Phase 8 introduces:
1. **Financial Educational Concepts & Lesson Modules**: Curated curriculum on asset allocation, inflation risk, compounding, fee drag, and diversification.
2. **Interactive AI Financial Tutor**: Conversational companion grounded in the user's specific risk profile, goals, and portfolio holdings.
3. **Comprehension Quizzes & Feedback**: Knowledge checks reinforcing financial literacy with feedback explanations.
4. **Learning Navigation**: Integration with dashboard and persistent module progress.
