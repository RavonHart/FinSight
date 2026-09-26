# FinSight — End-to-End AI Investment Research & Learning Platform

> **Master Engineering Architecture & Implementation**  
> *Production-Style Modular Monolith with LangGraph, Jev / TypeSafe AI, and Deterministic Financial Engine.*

---

## 1. System Philosophy

> **LLMs reason and explain. Jev makes structured judgments. Deterministic code performs financial calculations. External data sources provide evidence. LangGraph orchestrates the workflow. Humans make the final decisions.**

### Important Product Boundary
FinSight V1 is an investment research, portfolio analysis, forward simulation, and financial learning platform. It does **not** execute trades, connect with broker write-APIs, or hold custody of user funds.

---

## 2. Monorepo Structure

```text
finsight/
├── apps/
│   ├── web/                    # Next.js 14 App Router, Tailwind CSS, TypeScript
│   └── api/                    # FastAPI, SQLAlchemy 2.x, Celery, LangGraph
├── packages/
│   └── shared-types/           # Shared TypeScript interfaces & types
├── infrastructure/
│   ├── docker/                 # PostgreSQL + pgvector initialization scripts
│   ├── compose/                # Compose overrides & deployment configurations
│   └── deployment/             # Deployment manifests
├── docs/
│   ├── architecture/           # Overview, Backend, Frontend, Data specifications
│   ├── decisions/              # Architecture Decision Records (ADR-001 through ADR-008)
│   ├── agents/                 # LangGraph workflows and tool registry
│   ├── jev/                    # Jev questions, confidence routing, schemas
│   └── security/               # RLS policies, multi-tenant isolation, AI boundaries
├── .github/workflows/          # CI workflow pipeline
├── docker-compose.yml          # Local multi-service orchestration
├── .env.example                # Canonical environment variable specification
└── README.md
```

---

## 3. Quickstart (Phase 0 Acceptance)

### Using Docker Compose
Ensure Docker Desktop is running, then run:

```bash
docker compose up --build
```

### Verifying Service Acceptance Criteria

1. **Frontend**: Open `http://localhost:3000`  
   Displays: `FinSight — System Online`
2. **Backend**: Open `http://localhost:8000/health`  
   Returns:
   ```json
   {
     "status": "ok",
     "database": "ok",
     "redis": "ok"
   }
   ```
3. **Celery Worker**: Running background tasks (`ping`, `refresh_holding_prices`, `scheduled_watchlist_scan`).
4. **PostgreSQL + pgvector**: Port 5432 with Alembic migrations applied.
5. **Redis**: Port 6379 for Celery broker, caching, and SSE Pub/Sub.

---

## 4. Architecture Decision Records (ADRs)

- [ADR-001: Modular Monolith Architecture](file:///docs/decisions/ADR-001-modular-monolith.md)
- [ADR-002: PostgreSQL with pgvector for Relational and Vector Data](file:///docs/decisions/ADR-002-postgres-pgvector.md)
- [ADR-003: LangGraph for Agent Workflow Orchestration](file:///docs/decisions/ADR-003-langgraph.md)
- [ADR-004: Jev / TypeSafe AI for Structured Judgment Layer](file:///docs/decisions/ADR-004-jev.md)
- [ADR-005: Celery and Redis for Background Processing and SSE Streaming](file:///docs/decisions/ADR-005-celery-redis.md)
- [ADR-006: Explicit Product Boundary — No Real-Money Execution in V1](file:///docs/decisions/ADR-006-no-real-money-v1.md)
- [ADR-007: Supabase Auth with Local JWKS Verification](file:///docs/decisions/ADR-007-supabase-auth.md)
- [ADR-008: Defense-in-Depth Row-Level Security (RLS)](file:///docs/decisions/ADR-008-row-level-security.md)

---

## 5. Development Roadmap Status

- [x] **Phase 0: Foundation** (Monorepo, Docker Compose, DB Models, Alembic, FastAPI, Celery, Next.js, CI, Docs)
- [ ] **Phase 1: Authentication & RLS** (Supabase Auth, Local JWKS, Row-Level Security)
- [ ] **Phase 2: Financial Profile & Jev Assessment** (Questionnaire, Jev System One)
- [ ] **Phase 3: Portfolio & Holdings** (Deterministic valuation, allocations, transactions)
- [ ] **Phase 4: Agentic Research** (LangGraph research state, planner, tools, synthesis)
- [ ] **Phase 5: Jev Research Layer** (Question registry, confidence routing)
- [ ] **Phase 6: Research UX & Real-Time SSE** (Three-panel workspace, Redis Pub/Sub)
- [ ] **Phase 7: Deterministic Simulation** (Compound growth, scenario modeling)
- [ ] **Phase 8: Learning & AI Tutor** (Modules, progress tracking, quizzes)
- [ ] **Phase 9: Watchlists & Celery Beat** (Scheduled scanning, notifications)
- [ ] **Phase 10: Production Hardening** (LangSmith, OpenTelemetry, Cost ceilings)
