import psutil
from fastapi import APIRouter, Depends

from agent.core.security import verify_api_key

router = APIRouter(prefix="/agent/system", tags=["system"])


@router.get("/stats")
async def system_stats(api_key: str = Depends(verify_api_key)):
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": int(psutil.boot_time()),
    }
