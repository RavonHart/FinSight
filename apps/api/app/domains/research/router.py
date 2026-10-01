import uuid
import json
import asyncio
from typing import List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.db.session import get_db, async_session_factory
from app.api.dependencies import get_current_active_user
from app.db.models.users import User
from app.core.config import settings
from app.core.logging import logger
from app.domains.research.schemas import (
    ResearchProjectCreate,
    ResearchProjectResponse,
    ResearchRunCreate,
    ResearchRunResponse,
    ResearchTaskResponse,
    EvidenceResponse,
    SourceResponse,
    ClaimResponse,
)
from app.domains.research.service import (
    create_project,
    list_projects,
    get_project,
    delete_project,
    create_research_run,
    get_research_run,
    list_research_runs,
    execute_and_persist_research_run,
    get_run_tasks,
    get_run_evidence,
    get_run_sources,
    get_run_claims,
)

research_router = APIRouter(prefix="/research", tags=["Research"])


# ---------------------------------------------------------------------------
# Research Projects
# ---------------------------------------------------------------------------

@research_router.post("/projects", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    data: ResearchProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new research project workspace (§10, §43)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await create_project(db, user_uuid, data)


@research_router.get("/projects", response_model=List[ResearchProjectResponse])
async def list_projects_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all research projects for the authenticated user."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_projects(db, user_uuid)


@research_router.get("/projects/{project_id}", response_model=ResearchProjectResponse)
async def get_project_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves a single research project."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_project(db, user_uuid, project_id)


@research_router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a research project and associated runs."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    await delete_project(db, user_uuid, project_id)
    return None


# ---------------------------------------------------------------------------
# Research Runs (Creation & Execution)
# ---------------------------------------------------------------------------

async def _run_in_background(run_id: uuid.UUID):
    """Background task executor for asynchronous research run."""
    try:
        async with async_session_factory() as session:
            await execute_and_persist_research_run(session, run_id)
    except Exception as e:
        logger.error(f"Background research run execution failed for {run_id}: {e}")


@research_router.post("/projects/{project_id}/runs", response_model=ResearchRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run_endpoint(
    project_id: uuid.UUID,
    data: ResearchRunCreate,
    background_tasks: BackgroundTasks,
    execute_now: bool = Query(True, description="Whether to trigger execution automatically"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a new research run with idempotency deduplication (§45).
    Safely handles simultaneous race condition collisions via database unique constraint.
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    run, is_new = await create_research_run(db, user_uuid, project_id, data)

    # Only trigger execution if this is a newly created run and execute_now is True
    if is_new and execute_now:
        background_tasks.add_task(_run_in_background, run.id)

    return run


@research_router.post("/runs/{run_id}/execute", response_model=ResearchRunResponse)
async def execute_run_direct(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Synchronously triggers and awaits completion of a research run.
    Useful for testing and deterministic inspection.
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    await get_research_run(db, user_uuid, run_id)
    return await execute_and_persist_research_run(db, run_id)


@research_router.get("/runs/{run_id}", response_model=ResearchRunResponse)
async def get_run_endpoint(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves current status, metrics, and report metadata for a run."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_research_run(db, user_uuid, run_id)


@research_router.get("/projects/{project_id}/runs", response_model=List[ResearchRunResponse])
async def list_runs_for_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists research runs within a project."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_research_runs(db, user_uuid, project_id)


# ---------------------------------------------------------------------------
# Artifacts & Evidence Provenance (§10, §16, §57)
# ---------------------------------------------------------------------------

@research_router.get("/runs/{run_id}/tasks", response_model=List[ResearchTaskResponse])
async def get_run_tasks_endpoint(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all structured research tasks for a run."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_run_tasks(db, user_uuid, run_id)


@research_router.get("/runs/{run_id}/evidence", response_model=List[EvidenceResponse])
async def get_run_evidence_endpoint(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves extracted evidence items with source links and relevance scores."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_run_evidence(db, user_uuid, run_id)


@research_router.get("/runs/{run_id}/sources", response_model=List[SourceResponse])
async def get_run_sources_endpoint(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves immutable sources cited by evidence in the report."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_run_sources(db, user_uuid, run_id)


@research_router.get("/runs/{run_id}/claims", response_model=List[ClaimResponse])
async def get_run_claims_endpoint(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves atomic claims categorized by fact, analysis, scenario, uncertainty."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_run_claims(db, user_uuid, run_id)


# ---------------------------------------------------------------------------
# Server-Sent Events (SSE) Replay-Then-Subscribe Stream (§18, §23)
# ---------------------------------------------------------------------------

@research_router.get("/runs/{run_id}/stream")
async def stream_run_events(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Server-Sent Events endpoint with Replay-Then-Subscribe sequencing (§23).
    1. Queries DB to replay current run status and completed tasks.
    2. Subscribes to Redis Pub/Sub channel for real-time progress events.
    3. Gracefully closes when terminal state is reached.
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    run = await get_research_run(db, user_uuid, run_id)
    tasks = await get_run_tasks(db, user_uuid, run_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        # 1. Replay current database snapshot
        snapshot = {
            "event": "run_snapshot",
            "run_id": str(run.id),
            "status": run.status,
            "research_iterations": run.research_iterations,
            "tool_calls_used": run.tool_calls_used,
            "tasks": [{"id": str(t.id), "title": t.title, "status": t.status} for t in tasks],
            "report": run.model_metadata_json.get("report") if run.model_metadata_json else None,
        }
        yield f"event: snapshot\ndata: {json.dumps(snapshot)}\n\n"

        # If run is already completed or failed, finish stream immediately
        if run.status in ("completed", "completed_partial", "failed", "cancelled"):
            yield f"event: end\ndata: {json.dumps({'status': run.status})}\n\n"
            return

        # 2. Subscribe to Redis Pub/Sub for live updates
        channel_name = f"research_run:{run.id}"
        redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel_name)

        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    payload_str = message.get("data")
                    try:
                        event_data = json.loads(payload_str)
                        event_name = event_data.get("event", "message")
                    except Exception:
                        event_name = "message"

                    yield f"event: {event_name}\ndata: {payload_str}\n\n"

                    # Exit if run completed
                    if event_name in ("run_completed", "run_completed_partial", "run_failed"):
                        yield f"event: end\ndata: {json.dumps({'status': 'finished'})}\n\n"
                        break

                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.aclose()
            await redis_client.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
