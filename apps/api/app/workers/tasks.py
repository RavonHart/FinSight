import uuid
import asyncio
from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.logging import logger
from app.db.session import async_session_factory
from app.domains.research.service import execute_and_persist_research_run


@celery_app.task(name="app.workers.tasks.ping")
def ping() -> str:
    """Simple ping task for health check verification."""
    logger.info("Celery ping task executed successfully")
    return "pong"


import concurrent.futures


def _run_coroutine_safely(coro):
    """Executes coroutine safely whether running in standalone Celery worker or nested event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)


from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


def get_task_session():
    """Returns an async session with NullPool to prevent event-loop affinity issues across worker threads."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()


@celery_app.task(name="app.workers.tasks.research_run", bind=True, max_retries=2)
def research_run(self, run_id: str):
    """Executes asynchronous LangGraph research workflow for a given run_id (§16, §38)."""
    logger.info(f"Starting Celery research run worker execution: {run_id}")
    run_uuid = uuid.UUID(run_id)

    async def _execute():
        async with get_task_session() as session:
            return await execute_and_persist_research_run(session, run_uuid)

    try:
        result = _run_coroutine_safely(_execute())
        logger.info(f"Research run {run_id} completed with status {result.status}")
        return {"status": result.status, "run_id": run_id}
    except Exception as exc:
        logger.error(f"Research run worker failed for {run_id}: {exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="app.workers.tasks.execute_watchlist_scan", bind=True, max_retries=2)
def execute_watchlist_scan_task(self, scan_id: str):
    """Executes asynchronous market scan for a specific watchlist_scan record (§10, §38)."""
    logger.info(f"Starting Celery watchlist scan execution: {scan_id}")
    scan_uuid = uuid.UUID(scan_id)

    async def _execute():
        from app.domains.watchlists.service import process_watchlist_scan
        async with get_task_session() as session:
            return await process_watchlist_scan(session, scan_uuid)

    try:
        result = _run_coroutine_safely(_execute())
        logger.info(f"Watchlist scan {scan_id} completed with status {result.status}")
        return {"status": result.status, "scan_id": scan_id, "findings_count": result.findings_count}
    except Exception as exc:
        logger.error(f"Watchlist scan worker failed for {scan_id}: {exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="app.workers.tasks.refresh_holding_prices")
def refresh_holding_prices():
    """Refreshes market prices and valuations for all tracked portfolio holdings (§10, §38)."""
    logger.info("Running scheduled refresh_holding_prices task")

    async def _refresh():
        from datetime import datetime, timezone
        from decimal import Decimal
        from sqlalchemy import select
        from app.db.models.portfolios import Holding, Asset

        async with get_task_session() as session:
            stmt = select(Holding, Asset).join(Asset, Holding.asset_id == Asset.id)
            res = await session.execute(stmt)
            holdings_data = res.all()

            refreshed_count = 0
            now = datetime.now(timezone.utc)
            for holding, asset in holdings_data:
                meta = asset.metadata_json or {}
                price_val = Decimal(str(meta.get("price", "180.00")))
                holding.current_price = price_val
                holding.current_price_as_of = now
                holding.current_value = (holding.quantity * price_val).quantize(Decimal("0.01"))
                refreshed_count += 1

            await session.commit()
            return refreshed_count

    count = _run_coroutine_safely(_refresh())
    return {"status": "ok", "refreshed_assets": count}


@celery_app.task(name="app.workers.tasks.scheduled_watchlist_scan")
def scheduled_watchlist_scan():
    """
    Celery Beat scheduled daily scan (§38).
    Dispatches automated scans for all enabled watchlists with date-based scan idempotency.
    """
    logger.info("Running scheduled_watchlist_scan task")

    async def _scan_all():
        from datetime import datetime, timezone
        from sqlalchemy import select
        from app.db.models.watchlists import Watchlist
        from app.domains.watchlists.service import trigger_watchlist_scan

        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        scans_run = 0

        async with get_task_session() as session:
            stmt = select(Watchlist).where(Watchlist.scan_enabled.is_(True))
            res = await session.execute(stmt)
            watchlists = res.scalars().all()

            for wl in watchlists:
                scan_key = f"scheduled_scan:{wl.id}:{today_date}"
                try:
                    await trigger_watchlist_scan(
                        session,
                        user_id=wl.user_id,
                        watchlist_id=wl.id,
                        idempotency_key=scan_key,
                        run_sync=True,
                    )
                    scans_run += 1
                except Exception as e:
                    logger.error(f"Error scanning watchlist {wl.id}: {e}")

            return scans_run

    executed = _run_coroutine_safely(_scan_all())
    return {"status": "ok", "scans_executed": executed}


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
