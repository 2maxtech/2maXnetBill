from fastapi import APIRouter, Depends, Query

from agent.core.security import verify_api_key
from agent.services import content_filter, suricata

router = APIRouter(prefix="/security", tags=["security"], dependencies=[Depends(verify_api_key)])


# --- Suricata IDS/IPS ---

@router.get("/suricata/status")
async def suricata_status():
    return await suricata.get_status()


@router.get("/suricata/stats")
async def suricata_stats():
    return await suricata.get_stats()


@router.get("/suricata/alerts")
async def suricata_alerts(limit: int = Query(50, ge=1, le=500)):
    return await suricata.get_alerts(limit)


@router.get("/suricata/rules")
async def suricata_rules():
    return await suricata.get_rules()


@router.get("/suricata/rules/{filename}")
async def suricata_rule_file(filename: str):
    return {"content": await suricata.get_rule_file(filename)}


@router.put("/suricata/rules/{filename}")
async def suricata_save_rule(filename: str, body: dict):
    return {"result": await suricata.save_rule_file(filename, body["content"])}


@router.post("/suricata/reload")
async def suricata_reload():
    return {"result": await suricata.reload()}


@router.post("/suricata/start")
async def suricata_start():
    return {"result": await suricata.start()}


@router.post("/suricata/stop")
async def suricata_stop():
    return {"result": await suricata.stop()}


@router.post("/suricata/mode")
async def suricata_set_mode(body: dict):
    return {"result": await suricata.set_mode(body["mode"])}


# --- DNS Filtering ---

@router.get("/dns-filter/domains")
async def get_blocked_domains():
    return await content_filter.get_blocked_domains()


@router.get("/dns-filter/config")
async def get_dns_blocklist():
    return {"config": await content_filter.get_dns_blocklist()}


@router.post("/dns-filter/domain")
async def add_blocked_domain(body: dict):
    return {"result": await content_filter.add_blocked_domain(body["domain"])}


@router.delete("/dns-filter/domain")
async def remove_blocked_domain(body: dict):
    return {"result": await content_filter.remove_blocked_domain(body["domain"])}


@router.post("/dns-filter/apply")
async def apply_dns_blocklist(body: dict):
    return {"result": await content_filter.apply_dns_blocklist(body["domains"])}


# --- GeoIP Blocking ---

@router.get("/geoip/countries")
async def get_blocked_countries():
    return await content_filter.get_blocked_countries()


@router.get("/geoip/config")
async def get_geoip_config():
    return {"config": await content_filter.get_geoip_config()}


@router.post("/geoip/apply")
async def apply_geoip_block(body: dict):
    return {"result": await content_filter.apply_geoip_block(body["country_codes"])}
