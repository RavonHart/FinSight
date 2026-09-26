# FinSight Architecture Overview

## 1. System Objective & Philosophy
FinSight is a production-style, multi-user AI financial research, portfolio analysis, simulation, and investment-learning platform.

> **Guiding Principle:**
> LLMs reason and explain. Jev makes structured judgments. Deterministic code performs financial calculations. External data sources provide evidence. LangGraph orchestrates the workflow. Humans make the final decisions.

V1 does **not** execute trades, hold custody of funds, or autonomously invest.

---

## 2. High-Level Diagram

```text
                             USER
                              │
                              ▼
                  ┌───────────────────────┐
                  │        Next.js        │
                  │   Web App (apps/web)  │
                  └───────────┬───────────┘
                              │
                         HTTPS / SSE
                              │
                              ▼
                  ┌───────────────────────┐
                  │        FastAPI        │
                  │   REST API (apps/api) │
                  └───────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  PostgreSQL                Redis                Celery
  + pgvector                  │                     │
                              ▼                     ▼
                        Redis Pub/Sub         LangGraph Workflows
                              │                     │
                              └─────── SSE ◄────────┘
```

---

## 3. Core Architectural Layers

1. **Presentation Layer (`apps/web`)**: Next.js 14/15, React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Recharts. Pure presentation—no business logic.
2. **API & Orchestration Layer (`apps/api`)**: FastAPI providing JWT authentication, resource authorization, rate-limiting, and REST/SSE endpoints.
3. **Background & Agent Layer (`workers`, `agents`)**: Celery workers executing LangGraph research workflows asynchronously with bounded loops and Redis Pub/Sub progress streaming.
4. **Structured Judgment Layer (`jev`)**: TypeSafe AI / Jev executing calibrated, typed questions (probabilities, confidence, scores) without free-form hallucination.
5. **Deterministic Financial Engine (`finance`)**: Pure Python calculations using `Decimal` exclusively for valuation, return (CAGR, XIRR), asset allocation, and scenario simulation.
6. **Data & Storage Layer (`db`)**: PostgreSQL with pgvector for embeddings and Row-Level Security (RLS) as a defense-in-depth boundary.
