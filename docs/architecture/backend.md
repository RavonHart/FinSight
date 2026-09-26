# Backend Architecture

FinSight backend is implemented with FastAPI (Python 3.12+), SQLAlchemy 2.x (asyncpg), and Celery.

## Directory Structure
- `api/`: REST routing, dependencies, and SSE event streaming.
- `core/`: Configuration, security, logging, and error handling.
- `db/`: SQLAlchemy models, session management, and Alembic migrations.
- `domains/`: Domain services (portfolios, profiles, research, simulations, learning).
- `finance/`: Deterministic financial calculations using `Decimal` exclusively.
- `jev/`: TypeSafe AI / Jev structured judgment layer.
- `agents/`: LangGraph research workflow nodes and state transitions.
- `workers/`: Celery tasks and Beat scheduler.
