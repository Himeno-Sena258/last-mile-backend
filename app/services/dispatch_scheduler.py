import asyncio
import logging
from contextlib import asynccontextmanager

from app.db.database import SessionLocal
from app.models.car import Car
from app.models.enums import CarTaskStatus
from app.services.car_ws_manager import heartbeat_connections
from app.services.dispatch_service import DispatchService

logger = logging.getLogger(__name__)


async def run_scheduler():
    service = DispatchService()
    while True:
        try:
            with SessionLocal() as db:
                offline_car_ids = await heartbeat_connections(db)
                service.mark_cars_offline(db, offline_car_ids)
                service.reconcile_running_interruptions(db)
                await service.dispatch_pending(db)
        except Exception:
            logger.exception("Automatic dispatch cycle failed")
        await asyncio.sleep(5)


@asynccontextmanager
async def dispatch_lifespan(app):
    # Process-local WebSocket state is empty after a restart, so persisted cars
    # must prove liveness again before they can receive work.
    with SessionLocal() as db:
        db.query(Car).update({Car.task_status: CarTaskStatus.offline}, synchronize_session=False)
        db.commit()
    worker = asyncio.create_task(run_scheduler())
    try:
        yield
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass
