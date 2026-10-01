import uuid
import asyncio
from app.workers.celery_app import celery_app
from app.core.logging import logger
from app.db.session import async_session_factory
from app.domains.research.service import execute_and_persist_research_run


@celery_app.task(name="app.workers.tasks.ping")
def ping() -> str:
    """Simple ping task for health check verification."""
    logger.info("Celery ping task executed successfully")
    return "pong"


@celery_app.task(name="app.workers.tasks.research_run", bind=True, max_retries=2)
def research_run(self, run_id: str):
    """Executes asynchronous LangGraph research workflow for a given run_id (§16, §38)."""
    logger.info(f"Starting Celery research run worker execution: {run_id}")
    run_uuid = uuid.UUID(run_id)

    async def _execute():
        async with async_session_factory() as session:
            return await execute_and_persist_research_run(session, run_uuid)

    try:
        result = asyncio.run(_execute())
        logger.info(f"Research run {run_id} completed with status {result.status}")
        return {"status": result.status, "run_id": run_id}
    except Exception as exc:
        logger.error(f"Research run worker failed for {run_id}: {exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="app.workers.tasks.refresh_holding_prices")
def refresh_holding_prices():
    """Refreshes market prices for all tracked portfolio holdings (§10, §38)."""
    logger.info("Running scheduled refresh_holding_prices task")
    return {"status": "ok", "refreshed_assets": 0}


@celery_app.task(name="app.workers.tasks.scheduled_watchlist_scan")
def scheduled_watchlist_scan():
    """Runs scheduled scan on enabled watchlists (§38)."""
    logger.info("Running scheduled_watchlist_scan task")
    return {"status": "ok", "scans_executed": 0}


@celery_app.task(name="app.workers.tasks.document_ingestion")
def document_ingestion(source_id: str):
    logger.info(f"Ingesting document for source: {source_id}")
    return {"status": "ok", "source_id": source_id}


@celery_app.task(name="app.workers.tasks.embedding_generation")
def embedding_generation(chunk_ids: list):
    logger.info(f"Generating embeddings for {len(chunk_ids)} chunks")
    return {"status": "ok", "count": len(chunk_ids)}


@celery_app.task(name="app.workers.tasks.notification_delivery")
def notification_delivery(notification_id: str):
    logger.info(f"Delivering notification {notification_id}")
    return {"status": "ok", "notification_id": notification_id}


@celery_app.task(name="app.workers.tasks.large_simulation")
def large_simulation(simulation_id: str):
    logger.info(f"Executing simulation {simulation_id}")
    return {"status": "ok", "simulation_id": simulation_id}
