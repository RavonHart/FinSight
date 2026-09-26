# API Specification Overview

The FinSight API is exposed under `/api/v1`.

## Endpoints
- **Health**: `GET /health`, `GET /health/live`, `GET /health/ready`
- **Auth & Profiles**: `/api/v1/profile`, `/api/v1/profile/assessment`, `/api/v1/goals`
- **Portfolios**: `/api/v1/portfolios`, `/api/v1/portfolios/{id}/holdings`, `/api/v1/portfolios/{id}/transactions`, `/api/v1/portfolios/{id}/analytics`
- **Research**: `/api/v1/research/projects`, `/api/v1/research/projects/{id}/runs`, `/api/v1/research/runs/{id}`, `/api/v1/research/runs/{id}/events` (SSE), `/api/v1/research/runs/{id}/report`
- **Simulations**: `/api/v1/simulations`, `/api/v1/simulations/{id}`
- **Learning**: `/api/v1/learning`, `/api/v1/learning/{id}/quiz`, `/api/v1/learning/progress`
- **Watchlists**: `/api/v1/watchlists`, `/api/v1/watchlists/{id}/items`

## Pagination & Idempotency
- Keyset (cursor) pagination is supported on all collection endpoints (`limit`, `cursor`).
- Mutating endpoints (`POST /portfolios/{id}/transactions`, `POST /research/projects/{id}/runs`) require the `Idempotency-Key` header.
