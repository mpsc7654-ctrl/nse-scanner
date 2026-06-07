import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.database import AsyncSessionLocal
from app.services.scanner import scanner_service
from app.core.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def scan_task():
    async with AsyncSessionLocal() as db:
        try:
            await scanner_service.run_full_scan(db)
        except Exception as e:
            logger.error(f"Scan task error: {e}")

def start_scheduler():
    scheduler.add_job(
        scan_task,
        trigger=IntervalTrigger(seconds=settings.DATA_FETCH_INTERVAL),
        id="market_scan",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started: scan every {settings.DATA_FETCH_INTERVAL}s")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
