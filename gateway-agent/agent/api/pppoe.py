from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agent.core.config import settings
from agent.core.security import verify_api_key
from agent.services.accel_ppp import find_session_by_username, get_sessions, send_radius_packet

router = APIRouter(prefix="/agent/pppoe", tags=["pppoe"])


class CustomerAction(BaseModel):
    customer_id: str
    pppoe_username: str


class ThrottleAction(CustomerAction):
    download_mbps: int = 1
    upload_kbps: int = 512


@router.get("/sessions")
async def list_sessions(api_key: str = Depends(verify_api_key)):
    return await get_sessions()


@router.post("/disconnect")
async def disconnect(body: CustomerAction, api_key: str = Depends(verify_api_key)):
    session = await find_session_by_username(body.pppoe_username)
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    attrs = {
        "User-Name": body.pppoe_username,
        "Acct-Session-Id": session.get("sid", session.get("session_id", "")),
        "NAS-IP-Address": settings.NAS_IP,
    }
    result = send_radius_packet("disconnect", attrs, settings.RADIUS_SECRET, settings.RADIUS_SERVER, settings.RADIUS_COA_PORT)
    return {"status": "disconnected", "detail": result}


@router.post("/reconnect")
async def reconnect(body: CustomerAction, api_key: str = Depends(verify_api_key)):
    return {"status": "reconnect_ready", "detail": "Customer can now authenticate. Awaiting PPPoE redial."}


@router.post("/throttle")
async def throttle(body: ThrottleAction, api_key: str = Depends(verify_api_key)):
    session = await find_session_by_username(body.pppoe_username)
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    attrs = {
        "User-Name": body.pppoe_username,
        "Acct-Session-Id": session.get("sid", session.get("session_id", "")),
        "NAS-IP-Address": settings.NAS_IP,
        "WISPr-Bandwidth-Max-Down": str(body.download_mbps * 1_000_000),
        "WISPr-Bandwidth-Max-Up": str(body.upload_kbps * 1_000),
    }
    result = send_radius_packet("coa", attrs, settings.RADIUS_SECRET, settings.RADIUS_SERVER, settings.RADIUS_COA_PORT)
    return {"status": "throttled", "detail": result}
