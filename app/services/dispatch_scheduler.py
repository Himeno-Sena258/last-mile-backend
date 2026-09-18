import asyncio
import logging
from contextlib import asynccontextmanager

from app.db.database import SessionLocal
from app.services.dispatch_service import DispatchService

logger = logging.getLogger(__name__)


async def run_scheduler():
    service = DispatchService()
    while True:
        try:
            with SessionLocal() as db:
                await service.dispatch_pending(db)
        except Exception:
            logger.exception("Automatic dispatch cycle failed")
        await asyncio.sleep(5)


@asynccontextmanager
async def dispatch_lifespan(app):
    worker = asyncio.create_task(run_scheduler())
    try:
        yield
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass
