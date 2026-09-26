# ADR-001: Modular Monolith Architecture

## Context
FinSight requires multi-domain operations: financial profiles, portfolios, agentic research runs, deterministic financial calculations, simulations, and educational modules.

## Problem
Deciding whether to build a distributed microservice system or a single modular monolith for V1.

## Options Considered
1. **Microservices (Kubernetes, Kafka, independent services)**: High operational overhead, network latency, distributed transaction complexity, premature scaling.
2. **Modular Monolith (FastAPI modular packages, Celery workers, shared DB)**: Clear domain boundaries, simple local development, robust transactional integrity, low operational burden.

## Decision
We choose a **Modular Monolith** architecture with strict domain boundaries inside `apps/api/app/domains/` and async work offloaded to Celery workers.

## Why
A modular monolith provides high velocity, simple deployments via Docker Compose, and strong transaction consistency without the operational toll of distributed systems.

## Trade-offs
Services scale together rather than independently; however, compute-heavy tasks are isolated to Celery workers.

## Consequences
All domains must maintain strict module isolation (importing domain interfaces rather than reaching into database internals).

## Revisit Conditions
If an individual domain (e.g. document indexing or high-frequency real-time pricing) experiences independent scaling bottlenecks in production.
