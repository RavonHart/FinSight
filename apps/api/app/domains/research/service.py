import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.models.research import (
    ResearchProject,
    ResearchRun,
    ResearchTask,
    Source,
    DocumentChunk,
    Evidence,
    Claim,
    ClaimSource,
)
from app.db.models.jev import JevEvaluation
from app.domains.research.schemas import (
    ResearchProjectCreate,
    ResearchRunCreate,
)
from app.agents.graph import create_research_graph
from app.agents.state import ResearchState
from app.agents.events import publish_run_event
from app.core.logging import logger
from app.core.config import settings


# ---------------------------------------------------------------------------
# Research Project Service
# ---------------------------------------------------------------------------

async def create_project(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: ResearchProjectCreate,
) -> ResearchProject:
    """Creates a new research project container for an active user (§10, §43)."""
    project = ResearchProject(
        id=uuid.uuid4(),
        user_id=user_id,
        name=data.name,
        description=data.description,
        research_type=data.research_type,
        status="active",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def list_projects(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> List[ResearchProject]:
    """Lists all research projects belonging to the user."""
    stmt = (
        select(ResearchProject)
        .where(ResearchProject.user_id == user_id)
        .order_by(desc(ResearchProject.created_at))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_project(
    db: AsyncSession,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ResearchProject:
    """Retrieves a research project with user isolation."""
    stmt = (
        select(ResearchProject)
        .where(ResearchProject.id == project_id, ResearchProject.user_id == user_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research project {project_id} not found",
        )
    return project


async def delete_project(
    db: AsyncSession,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
) -> None:
    """Deletes a research project and cascading runs."""
    project = await get_project(db, user_id, project_id)
    await db.delete(project)
    await db.commit()


# ---------------------------------------------------------------------------
# Research Run Service (with Idempotency Race Guard)
# ---------------------------------------------------------------------------

async def create_research_run(
    db: AsyncSession,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ResearchRunCreate,
) -> Tuple[ResearchRun, bool]:
    """
    Submits a research run with race-condition-safe idempotency (§45).
    Returns (ResearchRun, is_created).
    If idempotency key already exists, returns existing run and is_created=False.
    """
    # Verify project exists and belongs to user
    await get_project(db, user_id, project_id)

    # 1. Pre-check optimization (avoids work if already known)
    if data.idempotency_key:
        stmt = select(ResearchRun).where(
            ResearchRun.idempotency_key == data.idempotency_key,
            ResearchRun.user_id == user_id,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            logger.info(f"Idempotency hit (pre-check) for key: {data.idempotency_key}")
            return existing, False

    run = ResearchRun(
        id=uuid.uuid4(),
        project_id=project_id,
        user_id=user_id,
        question=data.question,
        status="queued",
        idempotency_key=data.idempotency_key,
        research_iterations=0,
        tool_calls_used=0,
        model_metadata_json={},
        usage_metadata_json={},
    )
    db.add(run)

    # 2. Source-of-truth race condition defense via DB unique constraint
    try:
        await db.commit()
        await db.refresh(run)
        return run, True
    except IntegrityError as exc:
        await db.rollback()
        # In case of near-simultaneous duplicate request with same idempotency key
        if data.idempotency_key:
            stmt = select(ResearchRun).where(
                ResearchRun.idempotency_key == data.idempotency_key,
                ResearchRun.user_id == user_id,
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                logger.info(f"Idempotency hit (unique constraint violation caught) for key: {data.idempotency_key}")
                return existing, False
        logger.error(f"IntegrityError on research run insert: {exc}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict creating research run",
        )


async def get_research_run(
    db: AsyncSession,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
) -> ResearchRun:
    """Retrieves a research run belonging to the user."""
    stmt = (
        select(ResearchRun)
        .where(ResearchRun.id == run_id, ResearchRun.user_id == user_id)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run {run_id} not found",
        )
    return run


async def list_research_runs(
    db: AsyncSession,
    user_id: uuid.UUID,
    project_id: Optional[uuid.UUID] = None,
) -> List[ResearchRun]:
    """Lists research runs for a project or all runs for the user."""
    stmt = select(ResearchRun).where(ResearchRun.user_id == user_id)
    if project_id:
        stmt = stmt.where(ResearchRun.project_id == project_id)
    stmt = stmt.order_by(desc(ResearchRun.created_at))
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# LangGraph Execution & Durable Persistence (§10, §16, §17)
# ---------------------------------------------------------------------------

async def execute_and_persist_research_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> ResearchRun:
    """
    Executes the LangGraph research workflow and durably persists all
    sources, tasks, evidence, claims, and final markdown report into postgres (§10, §16).
    """
    # Fetch run
    stmt = select(ResearchRun).where(ResearchRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise ValueError(f"Research run {run_id} does not exist")

    # Mark running
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    await db.commit()

    # Calculate run wall-clock deadline
    deadline_ts = datetime.now(timezone.utc).timestamp() + settings.RUN_TIMEOUT_SECONDS
    deadline_iso = datetime.fromtimestamp(deadline_ts, tz=timezone.utc).isoformat()

    initial_state: ResearchState = {
        "user_id": str(run.user_id),
        "project_id": str(run.project_id),
        "run_id": str(run.id),
        "question": run.question,
        "research_iterations": 0,
        "tool_calls_used": 0,
        "run_deadline_at": deadline_iso,
        "status": "running",
        "errors": [],
        "sources": [],
        "evidence": [],
        "claims": [],
        "tasks": [],
    }

    # Execute StateGraph
    graph = create_research_graph()
    final_state: ResearchState = await graph.ainvoke(initial_state)

    # Persist durable records in Postgres (§10)
    # 1. Research Tasks
    for task_dict in final_state.get("tasks", []):
        task_id_str = task_dict.get("id")
        task_uuid = uuid.uuid4()
        task_obj = ResearchTask(
            id=task_uuid,
            research_run_id=run.id,
            task_type=task_dict.get("task_type", "research"),
            title=task_dict.get("title", "Research Step"),
            status="completed",
            assigned_agent="LangGraph Research Engine",
            input_json={"question": run.question},
            output_json={"status": "completed"},
            started_at=run.started_at,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(task_obj)

    # 2. Sources
    source_map: Dict[str, uuid.UUID] = {}
    for src in final_state.get("sources", []):
        src_temp_id = src.get("id", str(uuid.uuid4()))
        src_uuid = uuid.uuid4()
        source_map[src_temp_id] = src_uuid

        source_obj = Source(
            id=src_uuid,
            source_type=src.get("source_type", "sec_filing"),
            title=src.get("title", "External Source"),
            url=src.get("url"),
            publisher=src.get("publisher"),
            retrieved_at=datetime.now(timezone.utc),
            metadata_json={"run_id": str(run.id)},
        )
        db.add(source_obj)

    # Flush so sources have primary keys
    await db.flush()

    # 3. Evidence
    evidence_map: Dict[str, uuid.UUID] = {}
    for ev in final_state.get("evidence", []):
        ev_uuid = uuid.uuid4()
        ev_temp_id = ev.get("id", str(uuid.uuid4()))
        evidence_map[ev_temp_id] = ev_uuid
        src_uuid = source_map.get(ev.get("source_id"), list(source_map.values())[0] if source_map else uuid.uuid4())

        # If source didn't exist in map, create a fallback
        if not source_map:
            fb_src = Source(
                id=src_uuid,
                source_type="sec_filing",
                title="Primary SEC Disclosures",
                url=None,
                publisher="SEC EDGAR",
            )
            db.add(fb_src)
            await db.flush()

        ev_obj = Evidence(
            id=ev_uuid,
            research_run_id=run.id,
            source_id=src_uuid,
            claim=ev.get("claim", ""),
            evidence_text=ev.get("evidence_text", ""),
            relevance_score=Decimal(str(ev.get("relevance_score", "0.950"))),
            metadata_json={"extracted_at": datetime.now(timezone.utc).isoformat()},
        )
        db.add(ev_obj)

    # 4. Claims (with dynamic status evaluated by Jev)
    for cl in final_state.get("claims", []):
        cl_uuid = uuid.uuid4()
        conf_val = cl.get("confidence")
        claim_obj = Claim(
            id=cl_uuid,
            research_run_id=run.id,
            claim_text=cl.get("claim_text", ""),
            claim_type=cl.get("claim_type", "fact"),
            confidence=Decimal(str(round(float(conf_val), 3))) if conf_val is not None else None,
            status=cl.get("status", "supported"),
        )
        db.add(claim_obj)

    # 5. Jev System One Evaluations (§10, §13, §14)
    for jev_dict in final_state.get("jev_evaluations", []):
        jev_obj = JevEvaluation(
            id=uuid.uuid4(),
            research_run_id=run.id,
            financial_profile_id=None,
            question_id=jev_dict.get("question_id", "unknown"),
            input_state_json={"ticker": final_state.get("ticker", "NVDA")},
            result_type=jev_dict.get("result_type", "choice"),
            choice_value=jev_dict.get("choice_value"),
            score_value=Decimal(str(jev_dict["score_value"])) if jev_dict.get("score_value") is not None else None,
            probabilities_json=jev_dict.get("probabilities"),
            confidence=Decimal(str(round(jev_dict.get("confidence", 0.80), 4))),
            model_version=jev_dict.get("model_version", "jev-v1"),
            created_at=datetime.now(timezone.utc),
        )
        db.add(jev_obj)

    # 6. Update ResearchRun record
    report_dict = final_state.get("report", {})
    run.status = final_state.get("status", "completed")
    run.completed_at = datetime.now(timezone.utc)
    run.research_iterations = final_state.get("research_iterations", 0)
    run.tool_calls_used = final_state.get("tool_calls_used", 0)
    run.model_metadata_json = {
        "report": report_dict,
        "quality_checks": final_state.get("quality_checks", {}),
        "ticker": final_state.get("ticker", "NVDA"),
        "models_used": ["langgraph-researcher-v1", "jev-v1"],
        "source_count": len(final_state.get("sources", [])),
        "claims_count": len(final_state.get("claims", [])),
        "jev_evaluations_count": len(final_state.get("jev_evaluations", [])),
    }
    run.usage_metadata_json = {
        "tool_calls_used": final_state.get("tool_calls_used", 0),
        "iterations": final_state.get("research_iterations", 0),
        "duration_seconds": (datetime.now(timezone.utc) - run.started_at).total_seconds(),
    }

    await db.commit()
    await db.refresh(run)

    # Publish durable completion event to Redis Pub/Sub (§18, §23)
    await publish_run_event(
        run_id=str(run.id),
        event_type="run_completed" if run.status == "completed" else "run_completed_partial",
        payload=run.model_metadata_json,
    )

    return run


# ---------------------------------------------------------------------------
# Retrieval Services for Run Artifacts
# ---------------------------------------------------------------------------

async def get_run_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
) -> List[ResearchTask]:
    """Retrieves durable tasks for a run (§10)."""
    await get_research_run(db, user_id, run_id)
    stmt = (
        select(ResearchTask)
        .where(ResearchTask.research_run_id == run_id)
        .order_by(ResearchTask.started_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_run_evidence(
    db: AsyncSession,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
) -> List[Evidence]:
    """Retrieves durable evidence items linked to sources for a run (§10, §16)."""
    await get_research_run(db, user_id, run_id)
    stmt = (
        select(Evidence)
        .where(Evidence.research_run_id == run_id)
        .order_by(desc(Evidence.relevance_score))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_run_sources(
    db: AsyncSession,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
) -> List[Source]:
    """Retrieves sources referenced by evidence in a research run (§10)."""
    await get_research_run(db, user_id, run_id)
    stmt = (
        select(Source)
        .join(Evidence, Evidence.source_id == Source.id)
        .where(Evidence.research_run_id == run_id)
        .distinct()
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_run_claims(
    db: AsyncSession,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
) -> List[Claim]:
    """Retrieves claims generated for a run (§10)."""
    await get_research_run(db, user_id, run_id)
    stmt = (
        select(Claim)
        .where(Claim.research_run_id == run_id)
        .order_by(desc(Claim.confidence))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_run_jev_evaluations(
    db: AsyncSession,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
) -> List[JevEvaluation]:
    """Retrieves durable Jev evaluations for a run (§10, §13)."""
    await get_research_run(db, user_id, run_id)
    stmt = (
        select(JevEvaluation)
        .where(JevEvaluation.research_run_id == run_id)
        .order_by(JevEvaluation.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
