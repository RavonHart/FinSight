# Data Architecture & Models

FinSight uses PostgreSQL 16+ with the `pgvector` extension for both relational structures and vector embeddings.

## Schemas
1. **Identity & Auth**: `users`, `audit_logs`
2. **Profile & Goals**: `financial_profiles`, `financial_profile_assessments`, `goals`
3. **Portfolio & Holdings**: `assets`, `portfolios`, `holdings`, `transactions`
4. **Research Engine**: `research_projects`, `research_runs`, `research_tasks`, `sources`, `document_chunks`, `evidence`, `claims`, `claim_sources`, `jev_evaluations`
5. **Simulation & Monitoring**: `simulation_runs`, `watchlists`, `watchlist_items`, `watchlist_scans`, `notifications`
6. **Learning**: `learning_modules`, `learning_progress`, `quiz_attempts`

## Numeric Safety
- All currency, prices, quantities, and weights use `NUMERIC(20,8)` in PostgreSQL mapped to Python `Decimal`.
- Floating point data types (`FLOAT`, `REAL`, `DOUBLE PRECISION`) are prohibited for financial calculations.
