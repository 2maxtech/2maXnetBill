from fastapi import APIRouter, Depends

from app.core.dependencies import require_role
from app.models.user import UserRole
from app.services import gateway

router = APIRouter(prefix="/network", tags=["network"])
admin_only = Depends(require_role(UserRole.admin))


# --- Firewall ---
@router.get("/firewall/ruleset", dependencies=[admin_only])
async def get_firewall_ruleset():
    return await gateway.get_firewall_ruleset()

@router.get("/firewall/tables", dependencies=[admin_only])
async def get_firewall_tables():
    return await gateway.get_firewall_tables()

@router.post("/firewall/rule", dependencies=[admin_only])
async def add_firewall_rule(body: dict):
    return await gateway.add_firewall_rule(body["table"], body["chain"], body["rule"], body.get("family", "inet"))

@router.delete("/firewall/rule", dependencies=[admin_only])
async def delete_firewall_rule(body: dict):
    return await gateway.delete_firewall_rule(body["table"], body["chain"], body["handle"], body.get("family", "inet"))

@router.post("/firewall/flush", dependencies=[admin_only])
async def flush_firewall_chain(body: dict):
    return await gateway.flush_firewall_chain(body["table"], body["chain"], body.get("family", "inet"))


# --- Network ---
@router.get("/interfaces", dependencies=[admin_only])
async def get_interfaces():
    return await gateway.get_interfaces()

@router.get("/routes", dependencies=[admin_only])
async def get_routes():
    return await gateway.get_routes()

@router.post("/route", dependencies=[admin_only])
async def add_route(body: dict):
    return await gateway.add_route(body["destination"], body["gateway"], body.get("interface"))

@router.delete("/route", dependencies=[admin_only])
async def delete_route(body: dict):
    return await gateway.delete_route(body["destination"])

@router.get("/nat", dependencies=[admin_only])
async def get_nat():
    return await gateway.get_nat_rules()

@router.post("/nat/masquerade", dependencies=[admin_only])
async def add_masquerade(body: dict):
    return await gateway.add_nat_masquerade(body["out_interface"])

@router.post("/nat/port-forward", dependencies=[admin_only])
async def add_port_forward(body: dict):
    return await gateway.add_port_forward(body["protocol"], body["dport"], body["dest_ip"], body["dest_port"], body.get("in_interface"))


# --- DHCP ---
@router.get("/dhcp/leases", dependencies=[admin_only])
async def get_dhcp_leases():
    return await gateway.get_dhcp_leases()

@router.get("/dhcp/config", dependencies=[admin_only])
async def get_dhcp_config():
    return await gateway.get_dhcp_config()

@router.post("/dhcp/config", dependencies=[admin_only])
async def apply_dhcp_config(body: dict):
    return await gateway.apply_dhcp_config(body["config"])


# --- DNS ---
@router.get("/dns/config", dependencies=[admin_only])
async def get_dns_config():
    return await gateway.get_dns_config()

@router.post("/dns/entry", dependencies=[admin_only])
async def add_dns_entry(body: dict):
    return await gateway.add_dns_entry(body["domain"], body["ip"])

@router.get("/dns/upstream", dependencies=[admin_only])
async def get_upstream_dns():
    return await gateway.get_upstream_dns()
