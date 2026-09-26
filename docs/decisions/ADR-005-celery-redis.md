# ADR-005: Celery and Redis for Background Processing and SSE Streaming

## Context
Long-running research jobs, document chunking, price refreshing, and watchlist scanning cannot block HTTP request threads in FastAPI.

## Problem
Handling long-running background tasks reliably while streaming real-time execution progress to the frontend.

## Options Considered
1. **FastAPI BackgroundTasks**: Tied to the lifespan of the API web worker; lacks persistence, retry logic, concurrency limits, or scheduling.
2. **Celery with Redis**: Production-grade distributed task queue, task timeouts, retry policies, Beat scheduling, and Redis Pub/Sub for SSE event fanout.

## Decision
Use **Celery** with **Redis** as broker and result backend. Use Redis Pub/Sub as the real-time bridge between Celery workers and FastAPI SSE handlers.

## Why
Celery isolates CPU and network-intensive agent runs from user-facing API latency. Redis Pub/Sub allows workers to broadcast incremental progress events that FastAPI SSE streams immediately forward to browser clients.

## Trade-offs
Adds Celery worker and beat processes to deployment manifests.

## Consequences
Every background task must implement timeouts, retry policies with backoff, and persist execution status to Postgres (`research_runs`, `watchlist_scans`).

## Revisit Conditions
None for V1.
