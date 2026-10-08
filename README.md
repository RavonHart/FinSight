# FinSight — AI-Powered Financial Research & Investment Learning Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14_App_Router-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent_Workflows-blue.svg)](https://langchain-ai.github.io/langgraph/)
[![TypeSafe AI](https://img.shields.io/badge/TypeSafe_AI-System_One-7928CA.svg)](https://typesafe.ai)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_+_pgvector-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.3+-37814A.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose_Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **FinSight** is an institutional-grade, multi-agent financial research, portfolio analytics, and investment education platform. It unites dynamic LLM synthesis, calibrated **TypeSafe System One (Jev)** judgment, closed-form deterministic mathematics, and a real-time reactive Next.js 14 user interface into a cohesive, auditable system.

---

## 📑 Table of Contents

- [Core System Philosophy](#-core-system-philosophy)
- [System Architecture](#-system-architecture)
- [Key Features & Capabilities](#-key-features--capabilities)
  - [1. Autonomous Multi-Agent Research Engine](#1-autonomous-multi-agent-research-engine)
  - [2. TypeSafe System One (Jev) Judgment Layer](#2-typesafe-system-one-jev-judgment-layer)
  - [3. Deterministic Portfolio & Valuation Engine](#3-deterministic-portfolio--valuation-engine)
  - [4. Closed-Form Scenario & Monte Carlo Simulation](#4-closed-form-scenario--monte-carlo-simulation)
  - [5. Gamified Financial Learning Academy & AI Tutor](#5-gamified-financial-learning-academy--ai-tutor)
  - [6. Automated Watchlist Scanners & Background Tasks](#6-automated-watchlist-scanners--background-tasks)
  - [7. Defense-in-Depth RLS & Tamper-Evident Audit Packager](#7-defense-in-depth-rls--tamper-evident-audit-packager)
- [Monorepo Structure](#-monorepo-structure)
- [Quickstart with Docker Compose](#-quickstart-with-docker-compose)
- [Environment Configuration](#-environment-configuration)
- [REST API Specification](#-rest-api-specification)
- [Architecture Decision Records (ADRs)](#-architecture-decision-records-adrs)
- [Regulatory & Compliance Boundaries](#-regulatory--compliance-boundaries)

---

## 🏛 Core System Philosophy

Modern generative AI is prone to hallucination when computing numbers or enforcing strict regulatory boundaries. FinSight solves this through strict separation of concerns:
> 🧠 **LLMs Reason and Synthesize** &nbsp;⟷&nbsp; ⚖️ **Jev Evaluates and Validates** &nbsp;⟷&nbsp; 🔢 **Deterministic Code Computes**

1. **LLMs Reason and Synthesize**: Large Language Models (OpenAI GPT-4o) formulate hypotheses, plan multi-step research investigations, and synthesize narrative reports.
2. **TypeSafe System One (Jev) Judges**: Calibrated structured evaluation endpoints validate claims, assess cognitive biases, calculate confidence scores, and enforce regulatory boundaries.
3. **Deterministic Code Computes**: Financial metrics (IRR, CAGR, Sharpe ratio, Max Drawdown, compound interest, fee drag) are strictly calculated using Python's `Decimal` module with half-up rounding. Floating-point arithmetic is prohibited in valuation code.
4. **Verifiable External Evidence**: Research claims require ground-truth evidence gathered via real-time market quotes (Yahoo Finance), web research tools, and local pgvector embeddings.
5. **Humans Retain Sovereign Decision-Making**: FinSight is an informational research and learning system. It contains no broker execution endpoints and holds no custody of user assets.

---

## 📐 System Architecture

```mermaid
graph TD
    User([Investor / Learner]) -->|Next.js 14 App Router| WebApp[apps/web Frontend]
    WebApp -->|REST API & SSE Streams| API[apps/api FastAPI Gateway]
    
    subgraph Multi-Tenant Boundary [Defense-in-Depth Isolation]
        API -->|Local JWKS & Tenant Claim| DB[(PostgreSQL 16 + pgvector)]
        API -->|Pub/Sub & Task Enqueue| Redis[(Redis 7)]
    end

    subgraph Asynchronous Orchestration [Worker Cluster]
        Redis --> Worker[Celery Worker]
        Redis --> Beat[Celery Beat Scheduler]
        Worker -->|LangGraph Research Flow| GraphEngine[LangGraph State Machine]
        Beat -->|Scheduled Market Scan| Worker
    end

    subgraph Intelligence & Synthesis [External AI Services]
        GraphEngine -->|Synthesis & Planning| LLM[OpenAI / LLM Provider]
        GraphEngine -->|Structured Guardrails & Biases| Jev[TypeSafe AI / System One]
        GraphEngine -->|Live Market Data| Market[Yahoo Finance / Search APIs]
        GraphEngine -->|Observability Traces| LangSmith[LangSmith Tracing]
    end

    Worker -->|SSE Event Pipeline| Redis
    Redis -->|Live Progress Streaming| WebApp
```

---

## 🚀 Key Features & Capabilities

### 1. Autonomous Multi-Agent Research Engine
- **Cyclic LangGraph Orchestration**: Graph-based state machine containing `planner`, `tool_executor`, and `synthesizer` nodes.
- **Dynamic Research Planning**: Generates structured research goals, sub-queries, and tool-execution tasks.
- **Live SSE Streaming**: Emits real-time agent lifecycle events (`agent_thought`, `tool_call`, `tool_result`, `synthesis_chunk`) to the frontend workspace.
- **Evidence Provenance & Grounding**: Every quantitative assertion in generated markdown reports is mapped back to source URLs, timestamps, and raw payloads.

### 2. TypeSafe System One (Jev) Judgment Layer
- **High-Velocity Typed Evaluations**: Communicates directly with TypeSafe AI System One (`https://api.typesafe.ai/v1/systemone`).
- **Confidence Routing & Bias Detection**: Audits agent conclusions for Confirmation Bias, Recency Bias, and Overconfidence before presenting them to users.
- **Graceful Fallback Resilience**: Employs defensive circuit breakers with deterministic local fallback heuristics if external judgment quotas or networks are constrained.

### 3. Deterministic Portfolio & Valuation Engine
- **Bank-Grade Precision**: All valuations, cost bases, realized/unrealized PnL, and percentage weights use Python `Decimal` (`ROUND_HALF_UP`).
- **Institutional Risk Analytics**:
  - Annualized Sharpe Ratio and standard deviation of returns
  - Maximum Drawdown (MDD) tracking from peak historical valuations
  - Multi-asset class diversification breakdowns (Equities, Fixed Income, Crypto, Commodities, Cash)
- **Automatic Asset Rebalancing**: Evaluates target vs. actual allocations and highlights portfolio drift.

### 4. Closed-Form Scenario & Monte Carlo Simulation
- **Compound Growth Modeling**: Models deterministic wealth accumulation across flexible horizons (1 to 50 years).
- **Inflation & Purchasing Power**: Calculates real vs. nominal returns accounting for historical or user-specified inflation rates.
- **Fee Drag Analysis**: Quantifies the compounding destruction of management expense ratios (MER) over multi-decade periods.
- **Monte Carlo Probabilistic Pathways**: Generates confidence envelopes (5th, 25th, 50th, 75th, 95th percentiles) based on asset class volatility parameters.

### 5. Gamified Financial Learning Academy & AI Tutor
- **5-Tier Structured Curriculum**:
  1. *Financial Foundations & Cash Flow*
  2. *Asset Classes, Equities & Fixed Income*
  3. *Valuation Methodologies & Financial Statements*
  4. *Macroeconomics, Central Banking & Inflation*
  5. *Risk Management, Hedging & Portfolio Construction*
- **Interactive Knowledge Quizzes**: Validates concept comprehension with immediate rationales, scoring, and module completion tracking.
- **Socratic AI Tutor**: Embedded conversational assistant that clarifies complex financial concepts without dispensing illegal individualized investment advice.

### 6. Automated Watchlist Scanners & Background Tasks
- **Periodic Market Audits**: Celery Beat schedules recurring watchlist scans across user portfolios.
- **Metric Anomaly Alerts**: Monitors price thresholds, moving average breaches, and valuation changes.
- **Event-Driven Pub/Sub**: Pushes background scan findings directly to users through Redis.

### 7. Defense-in-Depth RLS & Tamper-Evident Audit Packager
- **PostgreSQL Row Level Security (RLS)**: Enforced at the database engine level via `SET LOCAL app.current_user_id`. Tenant data isolation cannot be bypassed even if application-level filters fail.
- **Advisory Refusal Auditing**: Explicitly records when the AI refuses to provide unauthorized financial advice, creating cryptographic legal evidence of compliance.
- **Cryptographic Tamper-Evidence**: Generates compliance audit bundles with SHA-256 digest hashing and verify endpoints to detect any post-generation tampering.

---

## 📂 Monorepo Structure

```text
FinSight/
├── apps/
│   ├── api/                            # FastAPI Backend Service
│   │   ├── app/
│   │   │   ├── agents/                 # LangGraph research state machine & nodes
│   │   │   ├── api/                    # API routes, dependencies & JWKS security
│   │   │   ├── core/                   # Settings, logging, and LLM factories
│   │   │   ├── db/                     # SQLAlchemy 2.0 models, async session & migrations
│   │   │   ├── domains/                # Domain routers (compliance, research, portfolios, etc.)
│   │   │   ├── finance/                # Pure Decimal deterministic math engine
│   │   │   ├── jev/                    # TypeSafe AI / Jev System One client & routing
│   │   │   ├── tools/                  # Market data & web search tools
│   │   │   └── workers/                # Celery background tasks & schedules
│   │   ├── Dockerfile                  # Production-optimized Python 3.11 container
│   │   └── requirements.txt            # Locked dependencies
│   │
│   └── web/                            # Next.js 14 Frontend Application
│       ├── app/
│       │   ├── app/                    # Authenticated dashboard, research, portfolio, etc.
│       │   ├── login/ & signup/        # Authentication pages
│       │   └── globals.css             # Tailored dark-mode glassmorphic design system
│       ├── components/                 # Three-panel workspace, plan visualizer, evidence panels
│       ├── lib/                        # API client wrappers & state utilities
│       └── Dockerfile                  # Multi-stage standalone Next.js container
│
├── infrastructure/
│   └── docker/
│       └── init-db.sql                 # PostgreSQL extensions (uuid-ossp, pgvector)
│
├── docs/
│   ├── architecture/                   # In-depth architectural specifications
│   ├── decisions/                      # Architecture Decision Records (ADR-001 - ADR-008)
│   └── security/                       # Defense-in-depth security & RLS model
│
├── docker-compose.yml                  # 6-service local production orchestration
├── .env.example                        # Canonical environment variable blueprint
└── README.md                           # Platform documentation
```

---

## ⚡ Quickstart with Docker Compose

FinSight is fully containerized. A single command launches the entire 6-container topology:

```bash
# 1. Clone the repository
git clone https://github.com/RavonHart/FinSight.git
cd FinSight

# 2. Configure your environment variables
cp .env.example .env
# Edit .env and supply your OPENAI_API_KEY and JEV_API_KEY

# 3. Launch the full stack
docker compose up --build -d
```

### Verified Container Topology

| Service | Container Name | Host Port | Role |
| :--- | :--- | :--- | :--- |
| **Frontend** | `finsight-web` | `3000` | Next.js 14 App Router UI |
| **API Gateway** | `finsight-api` | `8000` | FastAPI Backend & SSE Engine |
| **Worker** | `finsight-worker` | — | Celery Worker (LangGraph & Scans) |
| **Scheduler** | `finsight-beat` | — | Celery Beat Periodic Task Runner |
| **Database** | `finsight-postgres` | `5432` | PostgreSQL 16 + `pgvector` |
| **Broker / Cache**| `finsight-redis` | `6379` | Redis 7 Task Broker & SSE Channel |

### Health Check & Readiness

Confirm the entire cluster is healthy:

```bash
curl http://localhost:8000/health/ready
```

Expected response:
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "workers": "ok",
  "pool": {
    "size": 10,
    "checked_in": 10,
    "checked_out": 0,
    "clamped_overflow": 0,
    "raw_overflow": -9
  }
}
```

Open your browser at **`http://localhost:3000`** to begin.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the project root. Key configuration settings include:

```dotenv
# --- LLM Provider ---
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-proj-...

# --- TypeSafe AI / Jev System One ---
JEV_API_KEY=typesafe_...
JEV_BASE_URL=https://api.typesafe.ai/v1/systemone
JEV_MODEL=system-one-preview

# --- Observability & Tracing (Optional) ---
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=FinSight-Production

# --- Database & Redis ---
DATABASE_URL=postgresql+asyncpg://postgres:postgres@finsight-postgres:5432/finsight
REDIS_URL=redis://finsight-redis:6379/0

# --- Security & Auth ---
SECRET_KEY=change-this-in-production-to-a-secure-random-secret
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

---

## 📡 REST API Specification

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| **System** | | |
| `/health` | `GET` | Basic liveness probe |
| `/health/ready` | `GET` | Deep readiness check (DB, Redis, Celery, Pool Telemetry) |
| **Autonomous Research** | | |
| `/api/v1/research/jobs` | `POST` | Initiate agentic research job (dispatches Celery + LangGraph) |
| `/api/v1/research/jobs/{id}` | `GET` | Fetch research job status, markdown report, and citations |
| `/api/v1/research/jobs/{id}/events` | `GET` | Server-Sent Events (SSE) stream for real-time agent thoughts |
| **TypeSafe / Jev Auditing** | | |
| `/api/v1/jev/evaluate` | `POST` | Run typed evaluation on financial statements or research state |
| `/api/v1/jev/evaluations/{id}` | `GET` | Retrieve structured evaluation record |
| **Portfolios & Analytics** | | |
| `/api/v1/portfolios` | `GET` / `POST` | List and create investment portfolios |
| `/api/v1/portfolios/{id}/holdings` | `POST` | Add asset holding with deterministic cost basis |
| `/api/v1/portfolios/{id}/metrics` | `GET` | Fetch Sharpe ratio, Max Drawdown, and asset allocations |
| **Simulations** | | |
| `/api/v1/simulations/run` | `POST` | Run deterministic compound growth & fee drag simulation |
| `/api/v1/simulations/monte-carlo` | `POST` | Run probabilistic Monte Carlo pathway simulation |
| **Financial Academy** | | |
| `/api/v1/learning/modules` | `GET` | Retrieve curriculum modules and completion status |
| `/api/v1/learning/modules/{slug}/quiz` | `POST` | Submit quiz answers and receive instant scoring |
| `/api/v1/learning/tutor` | `POST` | Ask Socratic financial questions to the AI Tutor |
| **Compliance & Auditing** | | |
| `/api/v1/compliance/audit-packager/{id}` | `GET` | Export tamper-evident audit bundle with SHA-256 digest |
| `/api/v1/compliance/verify` | `POST` | Cryptographically verify authenticity of an audit bundle |

---

## 📚 Architecture Decision Records (ADRs)

Key architectural decisions are formally documented in [`docs/decisions/`](docs/decisions):

- [**ADR-001: Modular Monolith Architecture**](docs/decisions/ADR-001-modular-monolith.md) — Single deployable unit with strictly bounded internal domain contexts.
- [**ADR-002: PostgreSQL + pgvector**](docs/decisions/ADR-002-postgres-pgvector.md) — Unified storage engine for ACID relational data and dense vector embeddings.
- [**ADR-003: LangGraph for Agent Workflows**](docs/decisions/ADR-003-langgraph.md) — Deterministic cyclic state machines rather than unconstrained ReAct loops.
- [**ADR-004: TypeSafe AI / Jev for Structured Judgment**](docs/decisions/ADR-004-jev.md) — Decoupling generative prose synthesis from calibrated evaluation.
- [**ADR-005: Celery and Redis for Background Processing**](docs/decisions/ADR-005-celery-redis.md) — Durable queueing, scheduled market scans, and SSE streaming.
- [**ADR-006: Explicit Product Boundary (No Real Money Execution)**](docs/decisions/ADR-006-no-real-money-v1.md) — Strict informational boundary protecting regulatory positioning.
- [**ADR-007: Supabase Auth with Local JWKS Verification**](docs/decisions/ADR-007-supabase-auth.md) — Zero-latency sub-millisecond JWT authentication validation.
- [**ADR-008: Row-Level Security (RLS)**](docs/decisions/ADR-008-row-level-security.md) — Multi-tenant data isolation enforced by PostgreSQL kernel.

---

## ⚖️ Regulatory & Compliance Boundaries

> **Disclaimer**: FinSight is an educational, research, and simulation technology platform. It is **not** an investment advisor, broker-dealer, financial planner, or tax professional. FinSight does not provide personalized investment advice, offer securities for purchase, or execute financial transactions. All forward simulations, Monte Carlo models, and AI research reports are generated for educational and informational purposes only. Past performance and simulated projections are not indicative of future market returns.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
