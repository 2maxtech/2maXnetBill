import asyncio
import logging

import psutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select

from app.core.database import async_session
from app.models.customer import Customer, CustomerStatus
from app.services import gateway

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/system-stats")
async def ws_system_stats(websocket: WebSocket):
    """Push system stats every 5 seconds."""
    await websocket.accept()
    try:
        while True:
            stats = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "used": psutil.virtual_memory().used,
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "used": psutil.disk_usage("/").used,
                    "percent": psutil.disk_usage("/").percent,
                },
            }
            await websocket.send_json(stats)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket system-stats error: {e}")


@router.websocket("/ws/sessions")
async def ws_sessions(websocket: WebSocket):
    """Push active PPPoE session updates every 10 seconds."""
    await websocket.accept()
    try:
        while True:
            try:
                sessions = await gateway.get_active_sessions()
            except Exception:
                sessions = []

            # Also get customer count from DB
            async with async_session() as db:
                active_count = await db.execute(
                    select(func.count(Customer.id)).where(Customer.status == CustomerStatus.active)
                )
                total_count = await db.execute(select(func.count(Customer.id)))

                payload = {
                    "sessions": sessions if isinstance(sessions, list) else [],
                    "session_count": len(sessions) if isinstance(sessions, list) else 0,
                    "active_customers": active_count.scalar() or 0,
                    "total_customers": total_count.scalar() or 0,
                }

            await websocket.send_json(payload)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket sessions error: {e}")


@router.websocket("/ws/live-traffic")
async def ws_live_traffic(websocket: WebSocket):
    """Push aggregated traffic stats every 5 seconds."""
    await websocket.accept()
    try:
        prev_net = psutil.net_io_counters()
        await asyncio.sleep(1)

        while True:
            curr_net = psutil.net_io_counters()
            interval = 5

            bytes_in_per_sec = (curr_net.bytes_recv - prev_net.bytes_recv) / interval
            bytes_out_per_sec = (curr_net.bytes_sent - prev_net.bytes_sent) / interval

            payload = {
                "timestamp": asyncio.get_event_loop().time(),
                "bytes_in_per_sec": round(bytes_in_per_sec),
                "bytes_out_per_sec": round(bytes_out_per_sec),
                "mbps_in": round(bytes_in_per_sec * 8 / 1_000_000, 2),
                "mbps_out": round(bytes_out_per_sec * 8 / 1_000_000, 2),
                "total_bytes_in": curr_net.bytes_recv,
                "total_bytes_out": curr_net.bytes_sent,
            }

            await websocket.send_json(payload)
            prev_net = curr_net
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket live-traffic error: {e}")
