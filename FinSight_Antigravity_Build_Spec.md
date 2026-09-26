# FinSight --- End-to-End AI Investment Research & Learning Platform

## Antigravity Build Specification / Engineering Master Plan

> **Document status:** Build specification v1.1 (revised after
> architecture review — see §0 for a summary of what changed and why)\
> **Audience:** Antigravity / AI coding agent, software engineers,
> system designers\
> **Primary objective:** Build a production-style, multi-user AI
> financial research, portfolio analysis, simulation, and
> investment-learning platform.\
> **Important product boundary:** V1 does **not** hold user money,
> execute trades, or autonomously invest. It is a research, education,
> analysis, and simulation platform. Any future regulated advisory,
> broker integration, or real-money execution capability must be treated
> as a separate product phase and undergo appropriate legal/compliance
> review.

------------------------------------------------------------------------

# 0. Architecture Review Notes (v1.0 → v1.1)

This revision closes gaps found in a design review of v1.0. The product
vision, scope, and "LLM reasons, Jev judges, code calculates" philosophy
are preserved unchanged. What changed is implementation-readiness:
missing schema, an unbounded agent loop, an underspecified real-time
delivery path, numeric-safety rules, idempotency mechanics, and a few
places where "modular monolith" was undercut by unexamined vendor
choices.

Full rationale for each change is inline at the relevant section, and a
condensed list is at the end of this document. Read this section first,
then treat the rest of the document as authoritative.

------------------------------------------------------------------------

# 1. Executive Summary

Build **FinSight**, a full-stack AI-powered financial research
workspace.

The platform allows users to:

1.  Create an account.
2.  Build a structured financial profile.
3.  Define financial goals.
4.  Record a portfolio manually.
5.  Analyze portfolio composition and risk characteristics.
6.  Research companies, assets, industries, and financial questions.
7.  Run asynchronous agentic research workflows.
8.  Use **LangGraph** for workflow orchestration.
9.  Use a general-purpose LLM for planning, reasoning, retrieval
    synthesis, and explanations.
10. Use **Jev / TypeSafe AI System One** for typed, structured,
    confidence-aware judgments.
11. Use deterministic Python services for financial calculations.
12. Store evidence and source provenance for research claims.
13. Run investment/portfolio simulations.
14. Learn financial concepts through an integrated learning system and
    AI tutor.
15. Create virtual portfolios.
16. Maintain watchlists.
17. Observe research execution progress in real time.
18. Inspect high-level agent activity, evidence, and structured AI
    assessments.
19. Receive research updates in later versions.
20. Use the platform from a polished web UI.

The central design principle is:

> **LLMs reason and explain. Jev makes structured judgments.
> Deterministic code performs financial calculations. External data
> sources provide evidence. LangGraph orchestrates the workflow. Humans
> make the final decisions.**

------------------------------------------------------------------------

# 2. Product Vision

## Product statement

FinSight is an AI-powered personal financial research and learning
workspace that helps users understand their financial situation, analyze
portfolios, research investments and markets, simulate scenarios, and
learn investment concepts.

## Core principles

### Principle 1 --- Human decision remains central

The platform should support informed decision-making rather than present
an AI output as unquestionable truth.

### Principle 2 --- Evidence over hallucination

Important factual claims should have source provenance.

### Principle 3 --- LLM is not the source of truth

Do not ask an LLM to perform deterministic financial calculations when
code can perform them exactly.

### Principle 4 --- Jev is a structured judgment layer

Do not use Jev as a generic chatbot or report generator.

Use typed questions and structured outputs such as:

-   Choice
-   Score
-   probability distribution
-   confidence
-   Noul where appropriate

### Principle 5 --- Modular monolith first

Do not create microservices merely for architectural appearance.

Use a modular backend with clear domain boundaries.

### Principle 6 --- Async work should actually be async

Long-running research, document processing, embedding generation,
scheduled analysis, and large simulations should run through background
workers.

### Principle 7 --- Observability is a feature

Research execution should be traceable.

### Principle 8 --- Security is part of architecture

External documents, websites, and retrieved text are untrusted data.

------------------------------------------------------------------------

# 3. Product Scope

## V1 --- Must Have

### Authentication

-   Email/password
-   Google OAuth
-   Email verification
-   Password reset
-   Protected routes
-   Session management
-   Logout

### Financial profile

-   Investable capital
-   Monthly contribution
-   Investment horizon
-   Financial goals
-   Experience level
-   Liquidity requirement
-   Risk-related questionnaire
-   Jev-based structured profile assessment
-   Profile versioning/history

### Portfolio

-   Create portfolio
-   Add holdings
-   Edit/delete holdings
-   Record transactions
-   Portfolio valuation
-   Allocation
-   Basic returns
-   Asset-class exposure
-   Sector exposure
-   Concentration analysis

### Research

-   Create research projects
-   Start research runs
-   Research planner
-   Financial research
-   Market/industry research
-   News/recent-events research
-   Evidence collection
-   Source storage
-   Claim/source mapping
-   Jev evaluations
-   LLM synthesis
-   Final research report
-   Research history

### Simulation

-   Initial capital
-   Monthly contributions
-   Duration
-   Scenario assumptions
-   Inflation
-   Withdrawal scenarios
-   Compound-growth calculations
-   Scenario comparison

### Learning

-   Learning modules
-   Categories
-   Progress
-   AI explanations
-   Quizzes
-   Quiz scoring

### Virtual portfolio

-   Create virtual portfolio
-   Simulated transactions
-   Portfolio analytics

### UI/UX

-   Responsive dashboard
-   Research workspace
-   Portfolio dashboard
-   Simulation UI
-   Learning center
-   Settings
-   Real-time research progress
-   Evidence panel

### Engineering

-   Docker
-   PostgreSQL
-   pgvector
-   Redis
-   Celery
-   FastAPI
-   Next.js
-   LangGraph
-   Jev
-   LLM provider abstraction
-   LangSmith
-   GitHub Actions
-   automated tests

------------------------------------------------------------------------

# 4. Explicitly Out of Scope for V1

Do NOT implement:

-   Real-money trading
-   Broker write access
-   Autonomous trading
-   Automatic buying/selling
-   Options execution
-   Crypto trading
-   Custody of funds
-   Payment processing
-   Personalized regulated investment-advisory claims
-   Guaranteed returns
-   "Buy this stock" automation
-   Microservice decomposition
-   Kubernetes
-   Kafka
-   Fine-tuning custom LLMs
-   Mobile application
-   Social network
-   Copy trading

Design the architecture so future integrations are possible, but do not
implement them in V1.

------------------------------------------------------------------------

# 5. Technology Stack

## Frontend

-   Next.js
-   TypeScript
-   React
-   Tailwind CSS
-   shadcn/ui
-   TanStack Query
-   React Hook Form
-   Zod
-   Recharts
-   Lucide Icons

## Backend

-   Python 3.12+
-   FastAPI
-   Pydantic v2
-   SQLAlchemy 2.x
-   Alembic
-   httpx
-   pytest

## Agentic AI

-   LangGraph
-   LangChain where useful
-   General LLM through a provider abstraction
-   Jev / TypeSafe AI
-   Structured outputs
-   Tool calling

## Data

-   PostgreSQL
-   pgvector
-   Redis
-   S3-compatible object storage

## Background processing

-   Celery
-   Redis as broker/cache

## Observability

-   LangSmith
-   Python structured logging
-   OpenTelemetry in a later hardening phase

## Infrastructure

-   Docker
-   Docker Compose
-   GitHub Actions
-   Cloud deployment
-   Managed PostgreSQL
-   Managed Redis where appropriate

------------------------------------------------------------------------

# 6. High-Level Architecture

``` text
                              USER
                                |
                                v
                    +-----------------------+
                    |       Next.js         |
                    |       Web App         |
                    +-----------+-----------+
                                |
                         HTTPS / SSE
                                |
                                v
                    +-----------------------+
                    |        FastAPI        |
                    |     REST API Layer    |
                    +-----------+-----------+
                                |
        +-----------------------+------------------------+
        |                       |                        |
        v                       v                        v
  PostgreSQL                  Redis                  Celery
  + pgvector                    |                       |
        |                       |                       v
        |                       |                +--------------+
        |                       +--------------> |  LangGraph   |
        |                                        +------+-------+
        |                                               |
        |                     +-------------------------+
        |                     |            |            |
        v                     v            v            v
  Application              LLM          Jev          Tools
    Data                     |            |             |
                             |            |             |
                             +------------+-------------+
                                          |
                                          v
                                 Financial Engine
                                          |
                             +------------+------------+
                             |            |            |
                             v            v            v
                         Portfolio       Risk      Simulation
                          Engine        Engine       Engine
                                          |
                                          v
                                      Evidence
                                          |
                                          v
                                     Final Report

                              LangSmith
                                  |
                                  v
                         Traces / Evaluation
```

------------------------------------------------------------------------

# 7. Architectural Layers

## Layer 1 --- Presentation

Responsible for:

-   user interaction
-   visualization
-   forms
-   research progress
-   reports
-   portfolio charts
-   simulation charts

No financial business logic should live in React components.

------------------------------------------------------------------------

## Layer 2 --- API

FastAPI handles:

-   authentication validation
-   request validation
-   authorization
-   API contracts
-   resource ownership
-   job creation
-   synchronous operations
-   SSE streams

------------------------------------------------------------------------

## Layer 3 --- Domain Services

Contains:

-   portfolio service
-   profile service
-   research service
-   simulation service
-   learning service
-   watchlist service

------------------------------------------------------------------------

## Layer 4 --- Agentic System

LangGraph handles:

-   state
-   orchestration
-   routing
-   research planning
-   tool usage
-   Jev evaluations
-   evidence collection
-   synthesis
-   retry/research-more logic

------------------------------------------------------------------------

## Layer 5 --- Deterministic Financial Engine

Contains:

-   portfolio calculations
-   return calculations
-   allocation
-   risk metrics
-   simulation
-   inflation calculations
-   scenario analysis

------------------------------------------------------------------------

## Layer 6 --- Data

-   PostgreSQL
-   pgvector
-   object storage
-   Redis

------------------------------------------------------------------------

# 8. Repository Structure

Use a monorepo.

``` text
finsight/
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── types/
│   │   └── tests/
│   │
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── core/
│       │   ├── db/
│       │   ├── domains/
│       │   ├── agents/
│       │   ├── jev/
│       │   ├── tools/
│       │   ├── finance/
│       │   ├── workers/
│       │   └── schemas/
│       └── tests/
│
├── packages/
│   └── shared-types/
│
├── infrastructure/
│   ├── docker/
│   ├── compose/
│   └── deployment/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── agents/
│   ├── jev/
│   ├── security/
│   └── decisions/
│
├── scripts/
├── .github/
│   └── workflows/
│
├── docker-compose.yml
├── README.md
└── .env.example
```

------------------------------------------------------------------------

# 9. Backend Domain Structure

``` text
app/
│
├── main.py
│
├── api/
│   ├── dependencies.py
│   ├── router.py
│   ├── auth.py
│   ├── users.py
│   ├── profiles.py
│   ├── goals.py
│   ├── portfolios.py
│   ├── research.py
│   ├── simulations.py
│   ├── learning.py
│   ├── watchlists.py
│   └── events.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── logging.py
│   ├── exceptions.py
│   └── middleware.py
│
├── db/
│   ├── base.py
│   ├── session.py
│   ├── models/
│   ├── repositories/
│   └── migrations/
│
├── domains/
│   ├── users/
│   ├── profiles/
│   ├── goals/
│   ├── portfolios/
│   ├── research/
│   ├── simulations/
│   ├── learning/
│   └── watchlists/
│
├── agents/
│   ├── graph.py
│   ├── state.py
│   ├── planner.py
│   ├── financial_agent.py
│   ├── market_agent.py
│   ├── news_agent.py
│   ├── evidence_validator.py
│   ├── synthesizer.py
│   └── quality_check.py
│
├── jev/
│   ├── client.py
│   ├── questions.py
│   ├── schemas.py
│   ├── evaluators.py
│   └── routing.py
│
├── tools/
│   ├── registry.py
│   ├── market_data.py
│   ├── search.py
│   ├── filings.py
│   └── documents.py
│
├── finance/
│   ├── portfolio.py
│   ├── returns.py
│   ├── risk.py
│   ├── allocation.py
│   ├── simulation.py
│   ├── inflation.py
│   └── metrics.py
│
├── workers/
│   ├── celery_app.py
│   └── tasks.py
│
└── schemas/
```

------------------------------------------------------------------------

# 10. Database Schema

> **Review note:** v1.0's schema was missing three things a modular
> monolith needs before Phase 3 and Phase 4 can actually be built:
> a `document_chunks` table (pgvector is named as core infrastructure in
> §40 and used for semantic search/retrieval, but no table stored an
> embedding anywhere), the virtual-portfolio tables (Virtual Portfolio is
> listed as a V1 must-have in §3, but the original schema only modeled a
> single `portfolios`/`holdings` pair with no `is_virtual` distinction
> or simulated-transaction ledger), and scheduling/notification tables
> (Phase 9 requires a `scheduled_watchlist_scan` and
> `notification_delivery` Celery task, neither of which had anywhere to
> persist state). All three are added below. Status/enum columns that
> were previously bare `VARCHAR` with no defined value set are also
> called out, since an undefined enum is a bug waiting to happen in
> Alembic migrations and Pydantic schemas alike.

## users

``` text
id UUID PK
email VARCHAR UNIQUE
name VARCHAR
avatar_url TEXT NULL
auth_provider VARCHAR
created_at TIMESTAMP
updated_at TIMESTAMP
```

------------------------------------------------------------------------

## financial_profiles

``` text
id UUID PK
user_id UUID FK users.id UNIQUE

investable_capital NUMERIC
monthly_contribution NUMERIC

investment_horizon VARCHAR
primary_goal VARCHAR

experience_level VARCHAR
liquidity_requirement VARCHAR

risk_tolerance VARCHAR NULL
risk_capacity VARCHAR NULL

profile_version INTEGER

created_at TIMESTAMP
updated_at TIMESTAMP
```

Indexes:

``` text
user_id
```

------------------------------------------------------------------------

## financial_profile_assessments

``` text
id UUID PK
financial_profile_id UUID FK
assessment_version INTEGER

questions_json JSONB
answers_json JSONB
jev_results_json JSONB

confidence NUMERIC
created_at TIMESTAMP
```

------------------------------------------------------------------------

## goals

``` text
id UUID PK
user_id UUID FK

name VARCHAR
type VARCHAR

target_amount NUMERIC NULL
target_date DATE NULL

priority INTEGER

created_at TIMESTAMP
updated_at TIMESTAMP
```

------------------------------------------------------------------------

## assets

``` text
id UUID PK

symbol VARCHAR
name VARCHAR

asset_type VARCHAR
exchange VARCHAR NULL
currency VARCHAR

sector VARCHAR NULL
industry VARCHAR NULL

metadata_json JSONB

created_at TIMESTAMP
updated_at TIMESTAMP
```

Indexes:

``` text
symbol
asset_type
sector
```

------------------------------------------------------------------------

## portfolios

One table covers both real (manually-recorded) and virtual portfolios.
v1.0 modeled these as unrelated features — a `portfolios` table plus a
separate, never-specified "virtual portfolio" concept — despite both
being the same shape: a named collection of holdings with transactions.
Splitting them would have meant duplicating the entire analytics layer
(§19 Financial Engine) for no reason; a boolean discriminator is enough.

``` text
id UUID PK
user_id UUID FK

name VARCHAR
base_currency VARCHAR

portfolio_type VARCHAR   -- 'manual' | 'virtual'  (both are user-recorded, not broker-synced; see §59 for the future real-broker-synced type)
is_virtual BOOLEAN DEFAULT FALSE

created_at TIMESTAMP
updated_at TIMESTAMP
```

------------------------------------------------------------------------

## holdings

``` text
id UUID PK
portfolio_id UUID FK

asset_id UUID FK

quantity NUMERIC(20,8)
average_cost NUMERIC(20,8)

current_price NUMERIC(20,8) NULL
current_price_as_of TIMESTAMP NULL
current_value NUMERIC(20,8) NULL

created_at TIMESTAMP
updated_at TIMESTAMP
```

Unique:

``` text
(portfolio_id, asset_id)
```

`current_price` / `current_value` are a cache, not a source of truth —
see "Holding valuation refresh" below. `current_price_as_of` lets the UI
show "priced as of 4:02 PM" instead of implying a live quote.

------------------------------------------------------------------------

## transactions

``` text
id UUID PK
portfolio_id UUID FK
asset_id UUID FK

transaction_type VARCHAR  -- 'buy' | 'sell' | 'dividend' | 'split' | 'fee_adjustment'

quantity NUMERIC(20,8)
price NUMERIC(20,8)
fees NUMERIC(20,8) DEFAULT 0

transaction_date TIMESTAMP

idempotency_key VARCHAR NULL UNIQUE

created_at TIMESTAMP
```

`idempotency_key` (client-generated, e.g. a UUID the frontend holds
across a retried submit) is what actually satisfies §45's idempotency
requirement for transactions — v1.0 named the requirement but gave it
no mechanism. A unique constraint on it, checked before insert, is the
whole implementation; no distributed lock needed.

### Holding valuation refresh (missing in v1.0)

v1.0 stored `current_price`/`current_value` on `holdings` but never said
what keeps them current. That's a real gap: a portfolio dashboard
showing stale prices with no visible staleness is worse than one that's
honestly delayed. Required behavior:

- A scheduled Celery task (`refresh_holding_prices`, via Celery beat —
  see §38) re-fetches quotes for every distinct `asset_id` held by any
  non-virtual or virtual portfolio, at a configurable interval (V1
  default: hourly; markets close, don't poll every minute for no
  reason) and writes `current_price` + `current_price_as_of`.
- `current_value` is *never* trusted as stored on read for anything
  that feeds a financial calculation (§19) — it's recomputed from
  `quantity * current_price` in the Financial Engine at query time.
  The stored column exists purely so list views don't need an N+1 join
  through the Financial Engine for every holding on every page load.
- If a quote fetch fails for an asset, the holding keeps its last known
  price and `current_price_as_of` — it does not fall back to zero or
  null, which would silently corrupt allocation/return calculations.

------------------------------------------------------------------------

## research_projects

``` text
id UUID PK
user_id UUID FK

name VARCHAR
description TEXT

research_type VARCHAR
status VARCHAR

created_at TIMESTAMP
updated_at TIMESTAMP
```

------------------------------------------------------------------------

## research_runs

``` text
id UUID PK
project_id UUID FK
user_id UUID FK

question TEXT

status VARCHAR  -- 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'completed_partial'
  -- matches §43's run-state set, plus 'completed_partial' for the
  -- MAX_RESEARCH_ITERATIONS case in §17 — a run that finished but
  -- said so honestly about incomplete evidence is a distinct state
  -- from a clean success, and the UI/API contract should be able to
  -- tell them apart without parsing the report body.

idempotency_key VARCHAR NULL UNIQUE  -- client-supplied; see §45

started_at TIMESTAMP NULL
completed_at TIMESTAMP NULL

research_iterations INTEGER DEFAULT 0
tool_calls_used INTEGER DEFAULT 0

model_metadata_json JSONB
usage_metadata_json JSONB

error_message TEXT NULL

created_at TIMESTAMP
updated_at TIMESTAMP
```

Indexes:

``` text
(project_id, created_at)
(user_id, created_at)
(status)
```

------------------------------------------------------------------------

## research_tasks

``` text
id UUID PK
research_run_id UUID FK

task_type VARCHAR
title VARCHAR
status VARCHAR  -- 'pending' | 'running' | 'completed' | 'failed' | 'skipped'

assigned_agent VARCHAR

input_json JSONB
output_json JSONB
error_message TEXT NULL   -- v1.0 omitted this; §56 requires "partial
  -- result" UX ("show what succeeded and what failed"), which is
  -- impossible without a per-task error field to render

started_at TIMESTAMP NULL
completed_at TIMESTAMP NULL
```

------------------------------------------------------------------------

## sources

``` text
id UUID PK

source_type VARCHAR

title TEXT
url TEXT NULL
publisher TEXT NULL

published_at TIMESTAMP NULL
retrieved_at TIMESTAMP

content_hash VARCHAR NULL

metadata_json JSONB

created_at TIMESTAMP
```

------------------------------------------------------------------------

## document_chunks

Backs pgvector retrieval (§40). Every embedded unit — a filing excerpt,
a news article paragraph, a learning-module section — lives here, not
just conceptually referenced.

``` text
id UUID PK
source_id UUID FK sources.id NULL   -- NULL for internal content, e.g. learning modules
learning_module_id UUID FK learning_modules.id NULL

chunk_index INTEGER
content TEXT
token_count INTEGER

embedding VECTOR(embedding_dim)     -- dimension fixed by the chosen embedding model; document it in an ADR
embedding_model VARCHAR
embedding_version INTEGER

metadata_json JSONB

created_at TIMESTAMP
```

Constraint: exactly one of `source_id` / `learning_module_id` is set.

Indexes:

``` text
ivfflat or hnsw index on embedding (choose hnsw for V1 — better
  recall/latency at the write volumes this product will see; ivfflat
  only wins once index build time on a large corpus becomes the
  bottleneck)
source_id
learning_module_id
```

`embedding_model` and `embedding_version` are not decoration — they are
what makes it safe to change embedding models later without silently
mixing incompatible vectors in the same similarity search. Any query
against this table must filter by the model/version currently in use.

------------------------------------------------------------------------

## evidence

``` text
id UUID PK
research_run_id UUID FK
source_id UUID FK

document_chunk_id UUID FK document_chunks.id NULL

claim TEXT
evidence_text TEXT

relevance_score NUMERIC(4,3) NULL CHECK (relevance_score BETWEEN 0 AND 1)

metadata_json JSONB

created_at TIMESTAMP
```

------------------------------------------------------------------------

## claims

``` text
id UUID PK
research_run_id UUID FK

claim_text TEXT
claim_type VARCHAR  -- 'fact' | 'analysis' | 'scenario' | 'uncertainty'
  -- mirrors the four-way distinction §32 requires reports to make;
  -- v1.0 required the distinction in the UI but never tied it back to
  -- a stored, queryable value

confidence NUMERIC(4,3) NULL CHECK (confidence BETWEEN 0 AND 1)
status VARCHAR  -- 'supported' | 'unsupported' | 'contested' | 'unverified'

created_at TIMESTAMP
```

------------------------------------------------------------------------

## claim_sources

``` text
claim_id UUID FK
source_id UUID FK
evidence_id UUID FK

PRIMARY KEY(claim_id, source_id, evidence_id)
```

------------------------------------------------------------------------

## jev_evaluations

``` text
id UUID PK
research_run_id UUID FK NULL
financial_profile_id UUID FK NULL

question_id VARCHAR

input_state_json JSONB

result_type VARCHAR

choice_value VARCHAR NULL
score_value NUMERIC NULL

probabilities_json JSONB NULL

confidence NUMERIC

model_version VARCHAR

created_at TIMESTAMP
```

------------------------------------------------------------------------

## simulation_runs

``` text
id UUID PK
user_id UUID FK
portfolio_id UUID FK NULL

simulation_type VARCHAR
engine_version VARCHAR  -- pins the Financial Engine function/version
  -- used, so a stored simulation stays reproducible even after the
  -- simulation logic changes later (Report Metadata, §58, requires
  -- reproducibility for research reports; the same reasoning applies
  -- here and v1.0 didn't carry it over)

input_json JSONB
result_json JSONB

created_at TIMESTAMP
```

------------------------------------------------------------------------

## watchlists

``` text
id UUID PK
user_id UUID FK

name VARCHAR

scan_enabled BOOLEAN DEFAULT FALSE
scan_frequency VARCHAR NULL  -- 'daily' | 'weekly'; NULL when scan_enabled = FALSE

created_at TIMESTAMP
```

------------------------------------------------------------------------

## watchlist_items

``` text
id UUID PK
watchlist_id UUID FK
asset_id UUID FK

created_at TIMESTAMP
```

------------------------------------------------------------------------

## watchlist_scans

Missing in v1.0 despite Phase 9 explicitly requiring a
`scheduled_watchlist_scan` Celery task — there was nowhere for that
task's output to live.

``` text
id UUID PK
watchlist_id UUID FK

status VARCHAR  -- 'queued' | 'running' | 'completed' | 'failed'
findings_json JSONB   -- e.g. notable price moves, new filings, news hits
error_message TEXT NULL

started_at TIMESTAMP NULL
completed_at TIMESTAMP NULL
created_at TIMESTAMP
```

------------------------------------------------------------------------

## notifications

Also missing in v1.0, despite a `notification_delivery` Celery task
being named in §38. A notification needs somewhere to be created,
marked read, and looked up per-user — without this table "notification
delivery" has no delivery target.

``` text
id UUID PK
user_id UUID FK

notification_type VARCHAR  -- 'research_complete' | 'watchlist_finding' | 'system'
title VARCHAR
body TEXT

related_resource_type VARCHAR NULL
related_resource_id UUID NULL

read_at TIMESTAMP NULL
delivered_at TIMESTAMP NULL

created_at TIMESTAMP
```

Indexes:

``` text
(user_id, created_at)
(user_id, read_at)
```

------------------------------------------------------------------------

## learning_modules

``` text
id UUID PK

slug VARCHAR UNIQUE
title VARCHAR
category VARCHAR
difficulty VARCHAR

content TEXT

created_at TIMESTAMP
updated_at TIMESTAMP
```

------------------------------------------------------------------------

## learning_progress

``` text
id UUID PK
user_id UUID FK
module_id UUID FK

progress NUMERIC
completed BOOLEAN

last_accessed TIMESTAMP

UNIQUE(user_id, module_id)
```

------------------------------------------------------------------------

## quiz_attempts

``` text
id UUID PK
user_id UUID FK
module_id UUID FK

questions_json JSONB
answers_json JSONB

score NUMERIC

created_at TIMESTAMP
```

------------------------------------------------------------------------

## audit_logs

``` text
id UUID PK
user_id UUID FK NULL

action VARCHAR
resource_type VARCHAR
resource_id UUID NULL

metadata_json JSONB

created_at TIMESTAMP
```

------------------------------------------------------------------------

# 11. Authentication

Use **Supabase Auth** initially.

Backend flow:

``` text
User
 |
 v
Supabase Auth
 |
 v
JWT
 |
 v
FastAPI dependency
 |
 v
verify token
 |
 v
current_user
```

All user-owned queries MUST scope by authenticated user ID.

Never trust a `user_id` supplied by the frontend.

### Making "verify token" concrete

v1.0 named the step but not the mechanism, which matters because there
are two different, non-interchangeable ways to do it:

- **Preferred:** verify the JWT locally against Supabase's published
  JWKS endpoint (fetch and cache the public keys; verify signature,
  `exp`, `aud`, `iss` in the FastAPI dependency). No network call to
  Supabase per request — this is what keeps auth from becoming a
  latency and availability dependency on every single API call.
- **Avoid:** calling out to Supabase on every request to validate the
  token. It works, but it means Supabase's uptime becomes FinSight's
  uptime floor, for every request, which is a much larger blast radius
  than auth needs.

### Vendor-lock note (Principle 5 tension, worth naming explicitly)

Supabase Auth is a reasonable initial choice, but it sits slightly at
odds with "boring, portable infrastructure" (Rule 13, §62): user
identity becomes something FinSight doesn't own the source of truth
for. This is an acceptable V1 trade for auth (building auth in-house is
genuinely not where engineering effort should go early), but it should
be an explicit ADR (`ADR-007-supabase-auth.md`, add to §50) recording
*why*, and specifically noting the migration path (Supabase supports
exporting users; the `users` table's `auth_provider` column already
anticipates a second provider) so it isn't a surprise later.

### Defense in depth: don't rely on the app layer alone

"Never trust a `user_id` supplied by the frontend" is correct, but
v1.0's authorization model was single-layered — every ownership check
lives in application code (repository/service methods), which means
one missed `WHERE user_id = :current_user_id` clause in one endpoint is
a full cross-user data leak. For a financial application this is worth
a second layer:

- Enable PostgreSQL **Row-Level Security (RLS)** on every user-owned
  table, with a policy that filters on the session's `user_id` (set via
  `SET LOCAL` at the start of each request-scoped transaction, from the
  verified JWT `sub` claim). This doesn't replace application-layer
  checks — it's a backstop that turns "engineer forgot a WHERE clause"
  from a data breach into a no-op query.
- This is additive, not a rethink: it doesn't change the API, the
  domain services, or Rule 9 (§62). It's one Alembic migration adding
  policies, and one line at the top of the request lifecycle setting
  the session variable.

------------------------------------------------------------------------

# 12. Financial Profile Workflow

``` text
START
 |
 v
Load questionnaire
 |
 v
User answers questions
 |
 v
Validate input
 |
 v
Store raw answers
 |
 v
Construct structured state
 |
 v
Call Jev
 |
 v
Store Jev evaluations
 |
 v
Calculate application-level profile
 |
 v
Store profile version
 |
 v
Return profile
```

Jev should evaluate atomic dimensions such as:

-   investment horizon
-   liquidity requirement
-   risk tolerance
-   risk capacity
-   goal orientation
-   equity compatibility
-   diversification need

Do not ask Jev:

> "Tell me how this person should invest."

------------------------------------------------------------------------

# 13. Jev Architecture

Create a question registry.

``` text
jev/questions/
```

Questions:

``` text
risk_level
liquidity_requirement
risk_capacity
investment_horizon
growth_orientation
equity_compatibility
concentration_risk
evidence_sufficiency
financial_strength
growth_outlook
competitive_pressure
```

Every question must have:

``` text
id
description
input schema
output schema
version
thresholds
```

Example conceptual output:

``` json
{
  "question_id": "risk_level",
  "result": "HIGH",
  "probabilities": {
    "LOW": 0.05,
    "MODERATE": 0.21,
    "HIGH": 0.74
  },
  "confidence": 0.81
}
```

Never rely on parsing free-form model text for core decisions.

------------------------------------------------------------------------

# 14. Jev Confidence Routing

Implement:

``` text
Jev evaluation
 |
 +--> confidence >= HIGH_THRESHOLD
 |       |
 |       v
 |     continue
 |
 +--> confidence >= MEDIUM_THRESHOLD
 |       |
 |       v
 |     gather more evidence
 |
 +--> otherwise
         |
         v
       request clarification
       OR mark insufficient
```

Thresholds must be configurable.

Do not hardcode magic numbers throughout the codebase.

### Two different routing contexts (v1.0 conflated these)

This three-way routing tree reads cleanly, but it means two different
things depending on where a Jev call happens, and v1.0's Phase 2
description (§12) only really specified the profile case:

- **Profile assessment** (`financial_profile_assessments`, synchronous,
  user is present): "request clarification" is a real, immediate
  option — show the user a follow-up question and re-ask Jev. This is
  the case v1.0 already covered.
- **Research runs** (`jev_analysis` node, asynchronous, no user in the
  loop mid-run): there's no one to clarify with. "Request clarification
  OR mark insufficient" collapses to *mark insufficient* only — the
  low-confidence Jev result is recorded as-is (with its actual
  confidence value, never silently upgraded), and it becomes one input
  to `quality_check` (§17), which can trigger `research_more` (bounded
  by `MAX_RESEARCH_ITERATIONS`) to try to raise confidence by gathering
  more evidence before the next Jev pass. If it still comes back low
  after the iteration cap, the report surfaces it under "Uncertainties"
  (§57) rather than hiding it.

Both contexts share the same thresholds and the same Jev
questions/schemas (§13) — only what happens on the low branch differs.

------------------------------------------------------------------------

# 15. LangGraph Research State

Define:

``` python
class ResearchState(TypedDict, total=False):
    user_id: str
    project_id: str
    run_id: str

    question: str

    user_profile: dict
    portfolio_context: dict

    research_plan: list
    tasks: list

    sources: list
    evidence: list
    claims: list

    financial_analysis: dict
    market_analysis: dict
    news_analysis: dict

    jev_evaluations: list

    simulation_results: dict

    quality_checks: dict
    report: dict

    errors: list

    # Loop / budget control (see §17 "Loop termination") — required, not
    # optional, because they are what makes execute_research safe to
    # re-enter from quality_check.
    research_iterations: int
    tool_calls_used: int
    run_deadline_at: str  # ISO-8601, set once when the run starts
```

Use typed schemas for major objects.

`ResearchState` is Python-process-local LangGraph state, not the
persistence model — it does not survive a worker crash. `research_runs`
and `research_tasks` (see §10) are the durable record; a resumed or
inspected run reconstructs from those tables, not from this TypedDict.
Do not treat `ResearchState` as something the API layer can read
directly.

------------------------------------------------------------------------

# 16. LangGraph Nodes

## `load_context`

Loads:

-   user profile
-   goals
-   portfolio
-   research project
-   prior relevant research

------------------------------------------------------------------------

## `understand_question`

Uses LLM structured output to identify:

-   subject
-   research type
-   user intent
-   requested depth
-   relevant entities

------------------------------------------------------------------------

## `create_research_plan`

Creates a list of research tasks.

Example:

``` json
{
  "tasks": [
    {
      "type": "financial",
      "objective": "Analyze recent financial performance"
    },
    {
      "type": "industry",
      "objective": "Analyze competitive environment"
    },
    {
      "type": "news",
      "objective": "Find major recent developments"
    },
    {
      "type": "risk",
      "objective": "Identify material risks"
    }
  ]
}
```

------------------------------------------------------------------------

## `financial_research`

Uses financial data tools and filings.

------------------------------------------------------------------------

## `market_research`

Uses market/industry sources.

------------------------------------------------------------------------

## `news_research`

Uses recent news/search tools.

------------------------------------------------------------------------

## `collect_evidence`

Normalizes research outputs into:

-   source
-   evidence
-   claim

------------------------------------------------------------------------

## `validate_evidence`

Checks:

-   source existence
-   freshness
-   relevance
-   duplicate sources
-   claim/evidence alignment

------------------------------------------------------------------------

## `jev_analysis`

Runs appropriate Jev questions.

------------------------------------------------------------------------

## `financial_engine`

Performs deterministic calculations.

------------------------------------------------------------------------

## `quality_check`

Checks:

-   missing evidence
-   unsupported claims
-   conflicting evidence
-   insufficient confidence
-   incomplete research

------------------------------------------------------------------------

## `synthesize`

LLM converts validated evidence into a readable report.

The synthesis prompt MUST instruct the model to use only the provided
evidence/context for factual claims.

------------------------------------------------------------------------

## `save_report`

Persist:

-   report
-   claims
-   sources
-   Jev evaluations
-   usage
-   run status

------------------------------------------------------------------------

# 17. Research Graph

Initial graph:

``` text
START
  |
  v
load_context
  |
  v
understand_question
  |
  v
create_research_plan
  |
  v
execute_research
  |
  +---- financial_research
  |
  +---- market_research
  |
  +---- news_research
  |
  v
collect_evidence
  |
  v
validate_evidence
  |
  v
jev_analysis
  |
  v
financial_engine
  |
  v
quality_check
  |
  +---- insufficient AND research_iterations < MAX_RESEARCH_ITERATIONS
  |         |
  |         +---- research_more ---> back to execute_research
  |
  +---- insufficient AND research_iterations >= MAX_RESEARCH_ITERATIONS
  |         |
  |         +---- synthesize (report explicitly marked "incomplete evidence")
  |
  v
synthesize
  |
  v
save_report
  |
  v
END
```

Start simple. Do not implement a supervisor-agent architecture unless
the graph actually requires it.

### Loop termination (required)

The `quality_check → research_more → execute_research` cycle is the one
place in this graph where an agent can re-enter itself. v1.0 left this
loop uncapped, which is a real production hazard: a stubborn low-quality
research question (thin evidence, contradictory sources, a delisted
ticker) would otherwise retry indefinitely, burning LLM tokens and
holding a Celery worker until a hard timeout kills it.

Required guardrails, all part of `ResearchState`:

``` text
research_iterations: int        # incremented every time research_more fires
MAX_RESEARCH_ITERATIONS: int    # configurable, default 2 (i.e. 3 total passes)
max_tool_calls_used: int        # running total across the whole run
MAX_TOOL_CALLS: int             # configurable ceiling, hard-stops the run if exceeded
run_deadline_at: datetime       # wall-clock deadline set when the run starts
```

`quality_check` must check the iteration count *before* routing to
`research_more`. When the cap is hit, the graph proceeds to `synthesize`
with `quality_checks.status = "insufficient_evidence"` carried into the
report, not silently treated as success. The report must say so plainly
(see §57 report sections — "Uncertainties" is exactly this case). This
is a deliberate application of Principle 2 (evidence over hallucination):
an incomplete report that says it's incomplete is acceptable; a
complete-looking report built on a truncated loop is not.

`max_tool_calls_used` and `run_deadline_at` are separate ceilings
because a single research pass can itself run away (a tool that keeps
returning "needs more specific query"). Any node that calls a tool must
check the remaining budget first. This is the concrete mechanism behind
the AI Security requirements in §31 ("maximum tool calls", "maximum
research depth") — v1.0 stated the requirement but never defined where
the counters live or who increments them.

------------------------------------------------------------------------

# 18. LLM Responsibilities

LLM may:

-   understand natural language
-   generate research plans
-   classify research type
-   summarize evidence
-   explain financial concepts
-   synthesize reports
-   generate educational content
-   generate quiz questions
-   explain simulations

LLM must NOT be the authoritative calculator for:

-   CAGR
-   XIRR
-   portfolio allocation percentages
-   total contributions
-   return calculations
-   inflation adjustment
-   drawdown
-   risk metrics

Use deterministic Python functions.

------------------------------------------------------------------------

# 19. Financial Engine

Implement pure functions.

Example:

``` python
calculate_absolute_return(...)
calculate_cagr(...)
calculate_xirr(...)
calculate_portfolio_value(...)
calculate_allocation(...)
calculate_sector_exposure(...)
calculate_concentration(...)
calculate_drawdown(...)
calculate_inflation_adjusted_value(...)
simulate_contributions(...)
simulate_withdrawals(...)
```

Pure functions should be easy to unit test.

### Numeric precision (required — not stated in v1.0)

Money math in Python `float` silently drifts (`0.1 + 0.2 != 0.3`).
v1.0's Financial Engine section didn't specify a numeric type, which is
a real bug source in a spec that otherwise takes "deterministic
calculations" seriously — a deterministic function built on `float` is
still nondeterministic across platforms/versions in the last few bits,
and that's exactly the kind of thing that erodes trust once a user
notices their portfolio total shifts by a cent between page loads.

Rules:

- Every Financial Engine function takes and returns `decimal.Decimal`,
  never `float`. Convert at the I/O boundary only (Pydantic schemas can
  serialize `Decimal` directly to JSON as a string or number — pick one
  convention and hold it everywhere).
- Postgres `NUMERIC` columns map to `Decimal` through SQLAlchemy by
  default — don't override this to `Float`.
- Define a fixed rounding rule (`ROUND_HALF_EVEN`, applied once, at
  display/report time — not intermediate steps) and put it in one place
  (`finance/rounding.py`), not scattered across call sites.

### XIRR needs an explicit numerical method

`calculate_xirr` is not a closed-form formula — it's solved iteratively
(Newton's method or Brent's method against the NPV-zero condition), and
it can fail to converge for pathological cash-flow sequences (all
inflows, all outflows, sign-flip patterns with no real root). v1.0
listed it as one bullet alongside straightforward formulas like CAGR,
which understates the work. Required:

- Use a bounded iterative solver with a maximum iteration count and a
  defined fallback (return `None`/`insufficient_data` rather than
  raising, and have the caller — portfolio analytics, simulation UI —
  handle that case explicitly, since "XIRR unavailable" is a valid and
  fairly common real answer for young or transaction-sparse portfolios).
- Unit tests must include at least one case designed to not converge,
  to prove the fallback path is exercised, not just the happy path.

------------------------------------------------------------------------

# 20. Simulation Engine

Initial simulation:

Inputs:

``` text
initial_capital
monthly_contribution
duration_years
annual_return
inflation_rate
fees
```

Outputs:

``` text
total_contributions
nominal_value
real_value
growth
yearly_snapshots
```

Later add:

-   scenario ranges
-   Monte Carlo
-   contribution changes
-   withdrawals
-   market shocks

Do not claim simulated outcomes are forecasts or guarantees.

------------------------------------------------------------------------

# 21. Research Evidence Architecture

Every important claim should map to evidence.

``` text
Claim
 |
 +--- Evidence
 |      |
 |      +--- Source
 |
 +--- Evidence
        |
        +--- Source
```

Report UI should support:

> "Show evidence"

which reveals:

-   source
-   publication date
-   retrieval date
-   relevant excerpt
-   source type

Do not expose hidden chain-of-thought.

Expose **evidence and structured decision factors**, not private
internal reasoning.

------------------------------------------------------------------------

# 22. API Contracts

Base path:

``` text
/api/v1
```

Every `GET` list endpoint below (`/research/projects`, `/goals`,
`/watchlists`, etc.) takes standard `limit`/`cursor` pagination
parameters and returns a `next_cursor`. v1.0 didn't specify this, and
an unpaginated list endpoint on `research_runs` or `transactions` is a
guaranteed slow-query incident once a user has a real history. Use
cursor (keyset) pagination, not offset — offset pagination degrades on
large tables and is unstable under concurrent inserts.

## Profile

``` http
GET /profile
PUT /profile
POST /profile/assessment
GET /profile/assessment
```

## Goals

``` http
GET /goals
POST /goals
PUT /goals/{id}
DELETE /goals/{id}
```

## Portfolios

``` http
GET /portfolios
POST /portfolios
GET /portfolios/{id}
PUT /portfolios/{id}
DELETE /portfolios/{id}

POST /portfolios/{id}/holdings
PUT /portfolios/{id}/holdings/{holding_id}
DELETE /portfolios/{id}/holdings/{holding_id}

POST /portfolios/{id}/transactions
GET /portfolios/{id}/analytics
```

## Research

``` http
GET /research/projects
POST /research/projects
GET /research/projects/{id}
PUT /research/projects/{id}
DELETE /research/projects/{id}

POST /research/projects/{id}/runs      # requires Idempotency-Key header (see §45/§10 research_runs.idempotency_key) — a retried submit-on-flaky-connection must not create a second run for the same question

GET /research/runs/{id}
GET /research/runs/{id}/events         # SSE — see §23 for the resume/replay contract
GET /research/runs/{id}/report
POST /research/runs/{id}/cancel        # sets status='cancelled'; a running Celery task checks this on its next loop-termination check-in (§17) and stops rather than being force-killed
```

## Simulations

``` http
POST /simulations
GET /simulations/{id}
```

## Learning

``` http
GET /learning
GET /learning/{id}
POST /learning/{id}/quiz
GET /learning/progress
```

## Watchlists

``` http
GET /watchlists
POST /watchlists
GET /watchlists/{id}
POST /watchlists/{id}/items
DELETE /watchlists/{id}/items/{item_id}
```

------------------------------------------------------------------------

# 23. SSE Research Events

Endpoint:

``` http
GET /api/v1/research/runs/{run_id}/events
```

Events:

``` text
run_started
planning_started
task_created
task_started
source_found
evidence_found
jev_started
jev_completed
analysis_started
synthesis_started
report_ready
run_completed
run_failed
```

Example:

``` json
{
  "event": "task_started",
  "task_id": "...",
  "task_type": "financial_research",
  "message": "Analyzing financial information"
}
```

### The FastAPI ↔ Celery bridge (missing in v1.0)

This is worth being explicit about, because it's an easy thing to get
wrong: the process running `LangGraph` is a **Celery worker**, and the
process serving the SSE connection is a **FastAPI request handler** —
they are different OS processes, possibly on different machines, and
neither can just call a function on the other. v1.0's architecture
diagram drew a line from Celery straight to the browser's SSE stream,
which isn't a real connection without a mechanism in between.

Required pattern:

``` text
Celery worker (LangGraph node)
      |
      | publish event
      v
Redis Pub/Sub channel: research_run:{run_id}
      |
      | subscribe
      v
FastAPI SSE handler (GET /research/runs/{run_id}/events)
      |
      v
Browser (EventSource)
```

- Every LangGraph node that reaches a meaningful state boundary
  publishes a small JSON event to `research_run:{run_id}` on Redis
  Pub/Sub (Redis is already in the stack per §39 — this is additional
  *use* of it, not a new dependency).
- The FastAPI SSE endpoint subscribes to that channel for the duration
  of the client connection and forwards messages as SSE frames.
- **Also persist every event** to `research_tasks` / `research_runs`
  status columns as it's published, not only to Pub/Sub. Pub/Sub has no
  memory — a client that connects to `/events` *after* a node has
  already completed (page refresh mid-run, a second browser tab, a
  client that reconnects after a dropped connection) gets nothing from
  Pub/Sub alone. On connect, the SSE handler must first replay current
  state from the database (a synthetic "here's where things stand"
  event built from `research_tasks` rows) and then subscribe for
  further live updates. This resume behavior was entirely unspecified
  in v1.0 and is the difference between an SSE feature that works on a
  flaky connection and one that only works in a demo.

------------------------------------------------------------------------

# 24. Frontend Routes

``` text
/
 /login
 /signup

/app
/app/onboarding
/app/dashboard

/app/profile

/app/portfolio
/app/portfolio/[id]

/app/research
/app/research/[projectId]
/app/research/run/[runId]

/app/simulate

/app/learn
/app/learn/[module]

/app/watchlists

/app/settings
```

------------------------------------------------------------------------

# 25. Frontend UX

## Dashboard

Show:

-   financial profile summary
-   portfolio summary
-   active research
-   recent reports
-   watchlists
-   learning progress
-   quick actions

Quick actions:

``` text
[Research Something]
[Analyze Portfolio]
[Run Simulation]
[Learn]
```

------------------------------------------------------------------------

# 26. Research Workspace UX

Use a three-panel layout.

``` text
+----------------+---------------------------+----------------+
| Research Plan  | Report                    | Evidence       |
|                |                           |                |
| ✓ Financial    | Executive Summary         | Source 1       |
| ✓ Industry     |                           | Source 2       |
| ✓ News         | Financial Analysis        | Source 3       |
| ✓ Risk         |                           |                |
|                | Risks                     |                |
| AI Insights    | Uncertainties             |                |
|                |                           |                |
+----------------+---------------------------+----------------+
```

While running:

``` text
Planner                 ✓
Financial research      ✓
Market research         ✓
News research           ◉
Evidence validation     ○
Jev analysis            ○
Synthesis               ○
```

------------------------------------------------------------------------

# 27. Portfolio UX

Show:

-   total value
-   contribution
-   return
-   allocation
-   sector exposure
-   concentration
-   holdings table
-   transaction history

Charts:

-   allocation donut
-   value over time
-   contribution vs growth
-   sector exposure

------------------------------------------------------------------------

# 28. Simulation UX

Inputs:

-   capital
-   monthly contribution
-   duration
-   scenario assumptions
-   inflation
-   withdrawal

Output:

-   chart
-   table
-   total contributions
-   projected nominal values
-   inflation-adjusted values
-   assumptions

Always show assumptions prominently.

------------------------------------------------------------------------

# 29. Learning UX

Learning categories:

``` text
Basics
Risk
Portfolio
Stocks
Funds
Financial Statements
Valuation
Macroeconomics
```

Each module:

``` text
Concept
Example
Visual explanation
"Explain this differently"
Quiz
Progress
```

AI tutor can answer questions using the learning content.

------------------------------------------------------------------------

# 30. Security

## Authentication

-   JWT verification
-   secure session handling
-   protected routes

## Authorization

Every resource query must validate:

``` text
resource.user_id == current_user.id
```

Never trust client-supplied ownership IDs.

This application-layer check is necessary but not sufficient on its
own — see §11 "Defense in depth" for the Row-Level Security backstop,
which is a required part of the V1 security model, not a later
hardening item.

## API

-   rate limiting
-   request validation
-   maximum payload sizes
-   CORS restrictions
-   secure headers
-   timeouts
-   retry limits

## Secrets

Never commit:

``` text
API keys
JWT secrets
database passwords
LangSmith keys
Jev credentials
LLM credentials
```

Use environment variables.

Provide `.env.example`.

------------------------------------------------------------------------

# 31. AI Security

External documents and web pages are **untrusted content**.

Never allow retrieved content to directly execute tools.

Tool execution must be controlled by application code.

Implement:

-   tool allowlists
-   structured tool inputs
-   tool timeouts
-   maximum tool calls
-   maximum research depth
-   maximum token usage
-   prompt injection-resistant prompts
-   output validation

Do not give agents shell access in V1.

Do not give agents arbitrary Python execution.

### Per-run and per-user cost ceilings (missing in v1.0)

"Maximum token usage" was listed but never tied to an actual limit or a
consequence. Concretely:

- Every `research_runs` row tracks running token/tool-call totals
  (`usage_metadata_json`, already in the schema) updated as the graph
  executes, not only written once at the end — otherwise a runaway run
  is invisible until it finishes.
- `MAX_TOOL_CALLS` and a `MAX_TOKEN_BUDGET` per run (§17) are hard
  stops: when hit, the run transitions to `failed` (or
  `completed_partial` if past `quality_check`) rather than continuing.
  This is the enforcement mechanism behind the loop-termination
  guardrails in §17 — that section defines the counters, this one
  defines what happens when they're exceeded.
- A per-user daily/monthly cost ceiling (config-driven, ties into the
  rate limits in §46) protects against a single account — compromised
  key, buggy client retry loop, or just heavy usage — running up
  unbounded LLM spend. When exceeded, new research runs are rejected
  with a clear "usage limit reached" response, not silently queued
  forever.

------------------------------------------------------------------------

# 32. AI Output Safety

The system must avoid presenting:

-   guaranteed returns
-   certainty about future market performance
-   fabricated sources
-   unsupported factual claims
-   fake calculations
-   fake confidence

Research reports should clearly distinguish:

``` text
FACT
ANALYSIS
SCENARIO
UNCERTAINTY
```

Simulations must be described as simulations, not predictions.

------------------------------------------------------------------------

# 33. Observability

Integrate LangSmith with LangGraph.

Capture:

-   graph execution
-   node latency
-   LLM calls
-   tool calls
-   tokens
-   failures
-   retries
-   Jev calls
-   research run ID

Application logs should contain:

``` json
{
  "request_id": "...",
  "user_id": "...",
  "run_id": "...",
  "node": "financial_research",
  "status": "success",
  "duration_ms": 2400
}
```

Do not log:

-   passwords
-   access tokens
-   API keys
-   sensitive secrets

Minimize financial information in logs.

------------------------------------------------------------------------

# 34. Evaluation

Build an AI evaluation dataset.

Each test case contains:

``` text
question
expected research areas
expected sources
expected calculations
expected evidence
expected structured Jev dimension
```

Evaluate:

### Retrieval

-   relevance
-   completeness

### Evidence

-   source correctness
-   claim support

### LLM

-   factuality
-   groundedness
-   completeness
-   hallucination

### Jev

-   confidence
-   consistency
-   calibration
-   structured output validity

### Agent

-   correct tool choice
-   unnecessary tool calls
-   task completion
-   retry behavior

### Offline vs. online, and CI gating (missing in v1.0)

The dimensions above were listed with no execution model — when do they
run, and does a bad score block anything? Without that this section is
a wishlist, not an evaluation system. Required split:

- **Offline evaluation**: runs against the fixed dataset described
  above, on every PR that touches `agents/`, `jev/`, or `finance/`
  (CI job, §49). A regression past a configured threshold on
  groundedness or Jev structured-output validity fails the build — this
  is what makes evaluation a gate instead of a dashboard nobody checks.
- **Online evaluation**: sampled from real production runs (with user
  consent covered by the privacy policy, and PII-scrubbed before
  storage), scored asynchronously, feeding the same dashboards. This is
  what catches drift the fixed offline dataset won't (new company,
  new market condition, a provider's data format changing).
- Both write to the same evaluation store so trends are comparable over
  time, not two disconnected systems.

------------------------------------------------------------------------

# 35. Testing

## Backend unit tests

Test:

-   finance calculations
-   profile logic
-   portfolio logic
-   simulation
-   repository behavior
-   Jev adapters
-   schemas

## Integration tests

Test:

``` text
API
 ↓
Database
 ↓
Celery
 ↓
LangGraph
```

## Frontend tests

-   component tests
-   form tests
-   route tests

## E2E

Playwright flow:

``` text
Signup
 ↓
Onboarding
 ↓
Profile
 ↓
Create portfolio
 ↓
Create research project
 ↓
Run research
 ↓
View report
 ↓
Run simulation
```

------------------------------------------------------------------------

# 36. Docker

Local services:

``` text
frontend
api
worker
postgres
redis
```

Example architecture:

``` text
docker compose up
```

Should start the entire local development environment.

Use health checks.

Do not use development servers in production images.

### Liveness vs. readiness (v1.0 conflated these under one "/health")

A single `/health` endpoint (as used in §66's acceptance test) is fine
for the Phase 0 milestone, but for actual deployment orchestration
(anything beyond Docker Compose — see §48) liveness and readiness are
different questions and should be different endpoints:

- **Liveness** (`/health/live`): is the process running at all? No
  dependency checks — a database outage should not make the
  orchestrator kill and restart a perfectly healthy API process that's
  just waiting on a downed DB.
- **Readiness** (`/health/ready`): can this instance actually serve
  traffic right now? Checks DB and Redis connectivity. A failing
  readiness check should pull the instance out of the load balancer's
  rotation without restarting it.
- Keep the simple combined `/health` (§66) for the Phase 0 local
  milestone; split into the two above by Phase 10 (Production
  Hardening, §52) when real orchestration is in play.

------------------------------------------------------------------------

# 37. Environment Variables

`.env.example`:

``` text
APP_ENV=development

DATABASE_URL=
REDIS_URL=

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=

LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=

JEV_API_KEY=
JEV_MODEL=

LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
LANGSMITH_TRACING=true

OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
```

Never put real values into source control.

------------------------------------------------------------------------

# 38. Celery

Use Celery for:

``` text
research_run
document_ingestion
embedding_generation
scheduled_watchlist_scan
refresh_holding_prices        # added — see §10 "Holding valuation refresh"
notification_delivery
large_simulation
```

Every task must have:

-   timeout
-   retry policy
-   idempotency strategy
-   status persistence

### Scheduling (missing in v1.0)

`scheduled_watchlist_scan` and `refresh_holding_prices` are recurring,
not triggered by a user action — they need a scheduler, which v1.0
never named. Use **Celery beat** (already part of the Celery ecosystem,
no new infrastructure) to enqueue these on a configurable interval.
Beat's schedule store can be the database (`django-celery-beat`-style
persistence isn't available outside Django, so use a simple
`beat_schedule` config initially, backed by static config, and revisit
only if per-user variable schedules are actually needed).

### Connection pooling (missing in v1.0)

FastAPI (async, many short-lived DB connections per request) and Celery
(sync or async workers, longer-lived connections per task) have
different pooling needs, and both compete for the same Postgres
`max_connections` ceiling — a common production incident is a Celery
worker pool sized without accounting for FastAPI's pool, exhausting
Postgres connections under load. Required:

- Size FastAPI's SQLAlchemy pool and Celery's worker concurrency
  against a known `max_connections` budget, with headroom for managed
  Postgres's own reserved connections.
- Prefer PgBouncer (transaction-pooling mode) in front of Postgres once
  deployed beyond local Docker Compose, so pool sizing is centralized
  rather than split across two independently-configured pools.

------------------------------------------------------------------------

# 39. Redis

Use Redis for:

-   Celery broker
-   short-lived cache
-   rate limiting
-   transient job state

Do not use Redis as the authoritative application database.

------------------------------------------------------------------------

# 40. pgvector

Use pgvector for:

-   research document chunks
-   educational content
-   source retrieval
-   semantic search
-   relevant historical research context

Start with PostgreSQL + pgvector.

Do not introduce Qdrant unless scale or workload justifies it.

------------------------------------------------------------------------

# 41. Data Provider Abstraction

Financial data providers will change.

Do not scatter provider-specific API calls throughout the application.

Use:

``` text
providers/
├── market/
│   ├── base.py
│   └── provider_x.py
├── news/
├── filings/
└── search/
```

Interface example:

``` python
class MarketDataProvider(Protocol):
    async def get_quote(self, symbol: str): ...
    async def get_historical_prices(self, symbol: str, ...): ...
    async def get_fundamentals(self, symbol: str): ...
```

Agents depend on the interface, not the provider.

------------------------------------------------------------------------

# 42. Caching

Cache data that is:

-   expensive
-   repeatedly requested
-   safe to cache

Examples:

-   asset metadata
-   market quotes for a short interval
-   company profiles
-   research source metadata

Do not cache user-sensitive results without proper ownership boundaries.

------------------------------------------------------------------------

# 43. Error Handling

Every long-running run should have clear states:

``` text
QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED
```

Agent errors should be captured without exposing raw stack traces to
users.

User sees:

> "Research could not be completed because one of the data sources was
> unavailable."

Developer logs contain the detailed error.

------------------------------------------------------------------------

# 44. Retry Strategy

Retry:

-   transient HTTP errors
-   rate limits
-   temporary provider failures
-   worker failures

Do not blindly retry:

-   invalid user input
-   invalid tool schema
-   authentication errors
-   permanent provider errors

Use exponential backoff.

------------------------------------------------------------------------

# 45. Idempotency

Research jobs and transactions need idempotency protection.

A repeated Celery task should not:

-   duplicate transactions
-   duplicate reports
-   create duplicate research runs
-   double-process documents

Use unique job IDs and database constraints.

------------------------------------------------------------------------

# 46. Rate Limits

Initial conceptual limits:

``` text
Free user:
- limited research runs
- limited AI interactions
- limited document uploads
- limited simulations
- limited watchlist items
```

Make limits configurable.

Do not hardcode them into route handlers.

### Mechanism (v1.0 left this unspecified)

"Configurable, not hardcoded" describes a goal, not an implementation.
Concretely:

- Use a **sliding-window or token-bucket counter in Redis**
  (Redis is already in the stack, §39 — this is another legitimate use
  of it as short-lived state, not the authoritative database) keyed by
  `user_id` + limit type, with TTLs matching the window.
- Enforce limits in a single FastAPI dependency
  (`RateLimiter(limit_type)`), applied per-route, reading thresholds
  from config (not env vars sprinkled through route files) — this is
  what "do not hardcode" actually buys: changing a free-tier quota is a
  config change, not a deploy.
- On limit exceeded, return `429` with a `Retry-After` header, and log
  it distinctly from a generic error (useful signal for both abuse
  detection and legitimate-user friction).

------------------------------------------------------------------------

# 47. Admin

Build a minimal admin area.

Admin can inspect:

-   user count
-   active research runs
-   failed runs
-   AI usage
-   token usage
-   system errors
-   Jev evaluations
-   provider health

Admin must never expose user secrets.

### Admin access control (missing in v1.0)

An admin area with no stated access model is itself a security gap —
v1.0 never said who can reach `/admin` or how they're distinguished
from a normal authenticated user. Required minimum for V1:

- Add an `is_admin BOOLEAN DEFAULT FALSE` column to `users` (set only
  via direct database access or a seed script — never through a public
  API endpoint).
- A FastAPI dependency (`require_admin`) checks this flag in addition
  to normal authentication, applied to every admin route.
- Admin routes are still subject to the same audit logging (`audit_logs`,
  already in the schema) as any other mutating action — admin visibility
  into user data is itself something to have a trail of, precisely
  because it's an exception to normal per-user data isolation.

------------------------------------------------------------------------

# 48. Deployment

Initial deployment:

``` text
Next.js
  -> Vercel or equivalent

FastAPI
  -> Docker deployment

Celery Worker
  -> Docker deployment

PostgreSQL
  -> managed PostgreSQL

Redis
  -> managed Redis

Object storage
  -> S3-compatible provider

LangSmith
  -> hosted observability
```

Do not rely on an ephemeral/free database for important persistent user
data.

------------------------------------------------------------------------

# 49. CI/CD

GitHub Actions pipeline:

``` text
Push / PR
 |
 v
Lint
 |
 v
Type check
 |
 v
Unit tests
 |
 v
Integration tests
 |
 v
Frontend build
 |
 v
Backend Docker build
 |
 v
Security checks
 |
 v
Deploy
```

Branch model:

``` text
main
develop

feature/*
fix/*
refactor/*
```

------------------------------------------------------------------------

# 50. Documentation Requirements

Maintain:

``` text
README.md

docs/
├── architecture/
│   ├── overview.md
│   ├── backend.md
│   ├── frontend.md
│   └── data.md
│
├── agents/
│   ├── overview.md
│   ├── graph.md
│   ├── tools.md
│   └── evaluation.md
│
├── jev/
│   ├── integration.md
│   ├── questions.md
│   └── confidence.md
│
├── api/
│   └── overview.md
│
├── security/
│   └── model.md
│
└── decisions/
    ├── ADR-001-modular-monolith.md
    ├── ADR-002-postgres-pgvector.md
    ├── ADR-003-langgraph.md
    ├── ADR-004-jev.md
    ├── ADR-005-celery-redis.md
    ├── ADR-006-no-real-money-v1.md
    ├── ADR-007-supabase-auth.md          # added — see §11 vendor-lock note
    └── ADR-008-row-level-security.md     # added — see §30 defense-in-depth
```

------------------------------------------------------------------------

# 51. ADR Requirements

For every important architecture decision document:

``` text
# Decision

## Context

## Problem

## Options Considered

## Decision

## Why

## Trade-offs

## Consequences

## Revisit Conditions
```

------------------------------------------------------------------------

# 52. Development Phases

## Phase 0 --- Foundation

Deliver:

-   monorepo
-   Next.js
-   FastAPI
-   PostgreSQL
-   Redis
-   Docker Compose
-   SQLAlchemy
-   Alembic
-   CI
-   environment configuration

Acceptance:

``` text
docker compose up
```

starts the local system.

------------------------------------------------------------------------

## Phase 1 --- Authentication

Deliver:

-   Supabase Auth (JWKS-based local verification, §11)
-   login
-   signup
-   Google OAuth
-   protected routes
-   user profile
-   Row-Level Security policies on user-owned tables (§11, §30) —
    added here rather than deferred to Phase 10, since retrofitting RLS
    onto tables that already have data and application code assuming
    its absence is meaningfully more work than establishing the pattern
    once at the start

Acceptance:

A user can sign up and access the application, and a direct query
against a user-owned table with the wrong session context returns no
rows even if application-layer authorization were bypassed.

------------------------------------------------------------------------

## Phase 2 --- Financial Profile + Jev

Deliver:

-   onboarding
-   goals
-   financial profile
-   questionnaire
-   Jev integration
-   structured evaluations
-   confidence
-   profile persistence

Acceptance:

A user can complete onboarding and receive a structured profile
assessment.

------------------------------------------------------------------------

## Phase 3 --- Portfolio

Deliver:

-   portfolio CRUD
-   holdings
-   transactions
-   valuation
-   allocation
-   exposure
-   basic returns

Acceptance:

A user can create a virtual portfolio and see deterministic analytics.

------------------------------------------------------------------------

## Phase 4 --- Research

Deliver:

-   research projects
-   research runs
-   LangGraph
-   planner
-   research tools
-   evidence
-   citations
-   LLM synthesis

Acceptance:

User can submit:

> "Research NVIDIA."

and receive a source-backed report.

------------------------------------------------------------------------

## Phase 5 --- Jev Research Layer

Deliver:

-   Jev question registry
-   Jev research evaluations
-   confidence
-   routing
-   structured outputs
-   persistence

Acceptance:

Research run produces structured Jev evaluations and uses confidence to
influence workflow.

------------------------------------------------------------------------

## Phase 6 --- Research UX

Deliver:

-   SSE
-   progress view
-   research plan
-   evidence panel
-   report
-   run history
-   high-level agent activity

Acceptance:

User can watch the research run progress in real time.

------------------------------------------------------------------------

## Phase 7 --- Simulation

Deliver:

-   compound growth
-   recurring contributions
-   inflation
-   withdrawals
-   scenario comparison

Acceptance:

User can change assumptions and immediately compare scenarios.

------------------------------------------------------------------------

## Phase 8 --- Learning

Deliver:

-   learning modules
-   progress
-   AI tutor
-   quizzes

Acceptance:

User can learn a concept and complete a quiz.

------------------------------------------------------------------------

## Phase 9 --- Watchlists

Deliver:

-   watchlists
-   Celery beat schedule for `scheduled_watchlist_scan` and
    `refresh_holding_prices` (§38)
-   `watchlist_scans` and `notifications` persistence (§10)
-   notifications
-   research updates

Acceptance:

Background worker can process a watchlist without blocking the API, and
a completed scan is visible both as a persisted `watchlist_scans` row
and a `notifications` row the user can see and mark read — not just a
log line.

------------------------------------------------------------------------

## Phase 10 --- Production Hardening

Deliver:

-   LangSmith
-   evaluations
-   structured logging
-   OpenTelemetry
-   security
-   quotas
-   rate limiting
-   audit logs
-   deployment
-   backups
-   error monitoring

Acceptance:

The application is publicly accessible and operationally observable.

------------------------------------------------------------------------

# 53. MVP Vertical Slice

Before implementing every feature, build this complete path:

``` text
Signup
  |
  v
Onboarding
  |
  v
Financial Profile
  |
  v
Jev Assessment
  |
  v
Create Research Project
  |
  v
Ask Research Question
  |
  v
Celery Job
  |
  v
LangGraph
  |
  +--> Financial Research
  +--> Market Research
  +--> News Research
  |
  v
Evidence
  |
  v
Jev Evaluation
  |
  v
Financial Engine
  |
  v
LLM Synthesis
  |
  v
Persist Report
  |
  v
Research UI
```

This is the first major milestone.

------------------------------------------------------------------------

# 54. Definition of Done

A feature is not complete when code exists.

A feature is complete when:

-   API exists
-   Pydantic schemas exist
-   DB model exists where needed
-   migrations exist
-   authorization is implemented
-   tests exist
-   frontend UI exists
-   error states exist
-   loading states exist
-   empty states exist
-   logging exists
-   documentation exists
-   relevant observability exists

------------------------------------------------------------------------

# 55. UI Quality Requirements

The UI must feel like a serious SaaS product.

Avoid:

-   generic chatbot aesthetic
-   excessive gradients
-   unnecessary animations
-   clutter
-   unexplained AI outputs
-   giant walls of text

Prefer:

-   clean typography
-   strong hierarchy
-   whitespace
-   meaningful charts
-   clear status indicators
-   evidence cards
-   progressive disclosure
-   accessible forms
-   responsive design
-   keyboard accessibility

Use a consistent design system.

------------------------------------------------------------------------

# 56. Important UX States

Every major page needs:

### Loading

Skeleton or meaningful progress.

### Empty

Explain what to do next.

### Error

Human-readable explanation + retry.

### Success

Clear confirmation.

### Partial result

Show what succeeded and what failed.

Research pages especially must support partial execution.

------------------------------------------------------------------------

# 57. Research Report Structure

Generated report should follow:

``` text
Executive Summary

Research Question

Context

Key Findings

Financial Picture

Market / Industry Context

Recent Developments

Risk Factors

Uncertainties

Structured AI Assessments

Scenario Analysis

What Could Change the Conclusion

Sources
```

Do not generate a definitive "buy/sell" instruction.

------------------------------------------------------------------------

# 58. Report Metadata

Every report stores:

``` text
run_id
created_at
data_retrieved_at
models_used
source_count
claims_count
Jev_evaluation_count
simulation_count
execution_time
token_usage
```

This makes reports reproducible and auditable.

------------------------------------------------------------------------

# 59. Future Architecture --- Real Portfolio Integration

Do not implement in V1.

Future architecture:

``` text
Broker
 |
 v
Read-only Portfolio Sync
 |
 v
FinSight Portfolio
 |
 v
Research / Analytics
```

Only after this works should we investigate:

``` text
User confirmation
 |
 v
Broker API
 |
 v
Execution
```

Autonomous execution is a separate architecture and compliance problem.

------------------------------------------------------------------------

# 60. Future Architecture --- Advanced Agentic System

Potential future agents:

``` text
Research Agent
Financial Agent
Portfolio Agent
Risk Agent
Learning Agent
Monitoring Agent
Document Agent
```

But do not implement all of them initially.

Start with a graph of deterministic nodes and a small number of
specialized research nodes.

------------------------------------------------------------------------

# 61. Future Advanced Features

Potential later work:

-   broker read-only integration
-   portfolio import
-   bank statement ingestion
-   advanced tax analysis
-   financial document analysis
-   earnings-call analysis
-   SEC/annual-report ingestion
-   Indian regulatory document ingestion
-   Monte Carlo simulation
-   portfolio optimization
-   personalized learning paths
-   advanced notifications
-   research subscriptions
-   multi-language support
-   voice interface
-   mobile app
-   advanced observability
-   dedicated vector database if required

Any regulated advice/execution functionality must be separately reviewed
before implementation.

------------------------------------------------------------------------

# 62. Engineering Rules for Antigravity

## Rule 1

Do not rewrite working architecture without a concrete reason.

## Rule 2

Do not add dependencies without documenting why.

## Rule 3

Do not create microservices prematurely.

## Rule 4

Do not let LLM output directly modify financial state.

## Rule 5

Do not allow agents arbitrary tool execution.

## Rule 6

Do not use LLM-generated numbers as authoritative financial
calculations.

## Rule 7

Do not fabricate sources.

## Rule 8

Do not silently swallow exceptions.

## Rule 9

Every user-owned resource must enforce ownership.

## Rule 10

Every long-running operation must have persistent status.

## Rule 11

Every external provider should be abstracted.

## Rule 12

Every major architecture decision should have an ADR.

## Rule 13

Prefer boring, reliable infrastructure over unnecessary complexity.

## Rule 14

Build the vertical slice before expanding feature breadth.

## Rule 15

Every agentic loop (anything that can route back to an earlier node)
must have an explicit, configurable iteration cap and a defined
"give up honestly" exit path. An uncapped loop is not a simplification,
it's a missing requirement.

## Rule 16

All money and quantity values are `Decimal` end-to-end — database,
Python, API schemas. `float` never touches a financial calculation.

## Rule 17

Application-layer authorization checks are necessary but not sufficient
for user-owned financial data. Row-Level Security is the backstop, not
an optional hardening step.

------------------------------------------------------------------------

# 63. Antigravity Execution Strategy

When starting implementation:

### Step 1

Read this document completely.

### Step 2

Inspect the repository.

### Step 3

Create/update:

``` text
docs/architecture/overview.md
docs/architecture/decisions/
```

### Step 4

Create the monorepo structure.

### Step 5

Set up Docker Compose.

### Step 6

Set up PostgreSQL + Redis.

### Step 7

Set up FastAPI.

### Step 8

Set up Next.js.

### Step 9

Set up SQLAlchemy + Alembic.

### Step 10

Implement authentication.

### Step 11

Implement financial profile.

### Step 12

Implement Jev adapter.

### Step 13

Implement portfolio.

### Step 14

Implement LangGraph vertical slice.

### Step 15

Implement research UI.

### Step 16

Implement simulations.

### Step 17

Implement learning.

### Step 18

Implement watchlists/background jobs.

### Step 19

Implement observability/evaluation.

### Step 20

Deploy.

------------------------------------------------------------------------

# 64. Antigravity Working Method

For each feature:

``` text
Understand
   ↓
Design
   ↓
Implement
   ↓
Test
   ↓
Review
   ↓
Document
```

Do not implement huge numbers of files without testing intermediate
states.

After each phase:

1.  Run tests.
2.  Start services.
3.  Test API.
4.  Test UI.
5.  Check logs.
6.  Check database migrations.
7.  Update documentation.

------------------------------------------------------------------------

# 65. First Coding Task

Start with:

``` text
Phase 0 — Foundation
```

Implement:

``` text
finsight/
├── apps/
│   ├── web/
│   └── api/
├── packages/
├── infrastructure/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

Services:

``` text
web
api
worker
postgres
redis
```

The first milestone is:

``` text
docker compose up
```

and:

``` text
Frontend → loads
Backend → /health works
PostgreSQL → healthy
Redis → healthy
Celery worker → connected
```

Do not proceed to application features until this foundation works.

------------------------------------------------------------------------

# 66. First Milestone Acceptance Test

Expected:

``` text
GET /health

{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

Frontend:

``` text
FinSight
System Online
```

Worker log:

``` text
Celery worker connected
```

Database:

``` text
Alembic migrations applied
```

------------------------------------------------------------------------

# 67. Final Product Architecture

``` text
                                USER
                                  |
                                  v
                       +--------------------+
                       |      Next.js       |
                       |      Web App       |
                       +---------+----------+
                                 |
                              HTTPS/SSE
                                 |
                                 v
                       +--------------------+
                       |       FastAPI      |
                       +---------+----------+
                                 |
             +-------------------+--------------------+
             |                   |                    |
             v                   v                    v
       PostgreSQL              Redis               Celery
       + pgvector                |                    |
             |                   |                    v
             |                   +--------------> LangGraph
             |                                      |
             |                   +------------------+----------------+
             |                   |                  |                |
             |                   v                  v                v
             |                  LLM                JEV              Tools
             |                   |                  |                |
             |                   +------------------+                |
             |                                      |                |
             |                                      v                |
             |                              Financial Engine         |
             |                                      |                |
             |                         +------------+------------+   |
             |                         |            |            |   |
             |                         v            v            v   |
             |                     Portfolio      Risk      Simulation
             |                         |            |            |
             |                         +------------+------------+
             |                                      |
             +--------------------------------------+
                                                    |
                                                    v
                                                 Evidence
                                                    |
                                                    v
                                                 Report
                                                    |
                                                    v
                                                  USER

                         LangSmith / Observability
                                  |
                                  v
                      Traces / Evaluations / Costs
```

------------------------------------------------------------------------

# 68. Final Technology Decision

The initial stack is:

``` text
Frontend:
Next.js + TypeScript
Tailwind + shadcn/ui
TanStack Query
React Hook Form
Zod
Recharts

Backend:
Python
FastAPI
Pydantic
SQLAlchemy
Alembic

AI:
LangGraph
LLM provider abstraction
Jev / TypeSafe AI
Tool calling
RAG

Data:
PostgreSQL
pgvector
Redis
S3-compatible storage

Async:
Celery

Auth:
Supabase Auth

Observability:
LangSmith
Structured logging
OpenTelemetry later

Infrastructure:
Docker
Docker Compose
GitHub Actions
Cloud deployment

Testing:
Pytest
Vitest
Playwright
```

------------------------------------------------------------------------

# 69. Final Product Boundary

## FinSight V1 IS

``` text
Financial Profile
       +
Portfolio Analysis
       +
AI Research
       +
Evidence
       +
Jev Structured Judgments
       +
Financial Calculations
       +
Simulation
       +
Learning
       +
Virtual Portfolio
       +
Watchlists
```

## FinSight V1 IS NOT

``` text
Broker
Trading Platform
Custodian
Autonomous Trader
Guaranteed-return system
Unsupervised financial decision maker
```

------------------------------------------------------------------------

# 70. Success Criteria

FinSight is successful when a new user can:

``` text
1. Sign up
       ↓
2. Complete financial profile
       ↓
3. Receive a structured Jev assessment
       ↓
4. Create a virtual portfolio
       ↓
5. Analyze that portfolio
       ↓
6. Create a research project
       ↓
7. Ask a complex financial research question
       ↓
8. Watch LangGraph execute the research
       ↓
9. See evidence and sources
       ↓
10. See structured Jev insights
       ↓
11. Read a synthesized report
       ↓
12. Run a scenario simulation
       ↓
13. Learn concepts relevant to the analysis
       ↓
14. Return later and see research history
```

The entire journey should work from a public deployment.

------------------------------------------------------------------------

# 71. Final Engineering Philosophy

Build FinSight as a **real software system that happens to contain AI**,
not an AI demo wrapped in a website.

The architecture should demonstrate:

-   backend engineering
-   database design
-   asynchronous systems
-   agent orchestration
-   structured AI judgment
-   deterministic financial computation
-   RAG
-   evidence provenance
-   frontend engineering
-   authentication
-   security
-   observability
-   testing
-   CI/CD
-   deployment

The most important architectural relationship is:

``` text
                 HUMAN
                   |
                   v
              APPLICATION
                   |
          +--------+--------+
          |                 |
         LLM               JEV
          |                 |
   reasoning/synthesis   judgments
          |                 |
          +--------+--------+
                   |
            deterministic
              services
                   |
          +--------+--------+
          |                 |
       Financial          Data
        Engine           Sources
          |                 |
          +--------+--------+
                   |
                Evidence
                   |
                   v
                 HUMAN
```

**The human remains in control. The AI makes the research process more
capable, transparent, and educational.**

------------------------------------------------------------------------

# 72. Summary of Changes from v1.0

The product vision, scope, tech stack, and modular-monolith philosophy
are unchanged. What follows is what a design review added, and why —
grouped by what kind of gap each one closes.

## Correctness / safety-critical

- **Bounded research loop** (§17): `quality_check → research_more` had
  no iteration cap in v1.0 — a real infinite-loop/runaway-cost risk in
  production. Added `research_iterations`, `MAX_RESEARCH_ITERATIONS`,
  a tool-call budget, and a run deadline, all as explicit
  `ResearchState`/`research_runs` fields, with an honest
  `completed_partial` exit path rather than a silent failure or an
  unbounded retry.
- **Decimal-only financial math** (§19, Rule 16): v1.0 never pinned a
  numeric type. `float` in a financial engine is a correctness bug
  waiting to surface as a user-visible cent-level discrepancy.
- **XIRR treated as what it is** — an iterative solver with a real
  non-convergence case, not a one-line formula — with a defined
  fallback behavior instead of an unhandled exception.

## Missing schema (would have blocked Phase 3/4/9 as written)

- **`document_chunks`**: pgvector was named as core infrastructure
  (§40) with nothing to embed into. Added, with embedding
  model/version columns so a future embedding-model change doesn't
  silently corrupt similarity search.
- **Virtual portfolio support**: v1.0 listed "Virtual portfolio" as a
  V1 must-have (§3) but the schema had no way to represent one.
  Resolved by adding `is_virtual`/`portfolio_type` to the existing
  `portfolios` table rather than a parallel schema — same shape,
  same analytics code path, per Principle 5 (modular monolith, no
  duplicated subsystems for a boolean distinction).
- **`watchlist_scans` and `notifications`**: Phase 9 required
  `scheduled_watchlist_scan` and `notification_delivery` Celery tasks
  with nowhere in the schema for either to persist state.

## Architectural gap: real-time delivery had no real mechanism

- **FastAPI ↔ Celery ↔ SSE bridge** (§23): the v1.0 diagram implied a
  direct line from a Celery worker to a browser's SSE connection,
  which isn't how two separate processes talk. Added the Redis Pub/Sub
  bridge plus a database-backed resume/replay path for reconnecting
  clients — without the latter, SSE only works until the first dropped
  connection or page refresh.

## Underspecified requirements (stated as goals, not given a mechanism)

- **Idempotency** (§45, §10, §22): "needs idempotency protection" is a
  goal; a unique `idempotency_key` column plus an `Idempotency-Key`
  header contract is the mechanism. Applied to both `transactions` and
  `research_runs`.
- **Rate limiting** (§46): specified as Redis-backed sliding-window
  counters behind one FastAPI dependency, not left as "make it
  configurable."
- **Cost ceilings** (§31): "maximum token usage" now has an actual
  per-run and per-user enforcement path, tied to the same counters
  used for loop termination.
- **Admin access control** (§47): an admin area with no stated access
  model is a gap by itself; added an `is_admin` flag, a dependency
  gate, and audit logging of admin actions.
- **Evaluation execution model** (§34): split into CI-gated offline
  evaluation and sampled online evaluation, so the evaluation
  dimensions listed in v1.0 actually run somewhere and can block a
  regression, rather than describing metrics nobody computes.

## Defense in depth

- **Row-Level Security** (§11, §30, Rule 17): application-layer
  ownership checks are correct but single-layered — one missed `WHERE`
  clause is a full data leak in a financial application. RLS is added
  as a required Phase 1 deliverable, not a later hardening pass,
  because retrofitting it after tables have data and code assumes its
  absence is much more expensive than establishing it early.
- **JWT verification mechanics** (§11): specified as local JWKS
  verification rather than a per-request call to Supabase, so auth
  doesn't become a latency/availability dependency on every request.

## Named but not resolved as trade-offs

- **Supabase Auth vendor lock-in** (§11): kept as the V1 choice (it's
  the right call — building auth in-house early is a poor use of
  effort) but now explicitly flagged as a tension with Principle 5 and
  given its own ADR and a stated migration path, rather than left
  implicit.
- **Connection pooling** (§38): FastAPI's and Celery's pools compete
  for the same `max_connections` ceiling; sizing guidance and a
  PgBouncer recommendation added for anything past local Docker
  Compose.
- **Liveness vs. readiness** (§36): the single `/health` check is fine
  for the Phase 0 milestone but was never going to be sufficient for
  real orchestration; split into two endpoints, deferred to Phase 10
  where it actually matters.

## What was deliberately left alone

No microservices were introduced. No new infrastructure component was
added (Redis Pub/Sub and Celery beat are uses of what was already in
the stack, not new services). No agent, node, or table was added that
isn't directly required by a V1 must-have feature or a gap that would
have blocked one. The three-way LLM / Jev / deterministic-code
separation, and the "human decides" principle, are unchanged and, if
anything, more consistently enforced by the additions above (the
quality-check loop cap and the cost ceilings both exist specifically to
keep the AI layer bounded and legible rather than open-ended).

------------------------------------------------------------------------

# END OF BUILD SPECIFICATION
