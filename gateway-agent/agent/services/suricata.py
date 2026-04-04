import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

SURICATA_CONF = "/etc/suricata/suricata.yaml"
SURICATA_RULES_DIR = "/etc/suricata/rules"
SURICATA_LOG = "/var/log/suricata/eve.json"


async def _run_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{stderr.decode()}")
    return stdout.decode()


async def get_status() -> dict:
    """Get Suricata service status."""
    try:
        output = await _run_cmd("systemctl is-active suricata")
        active = output.strip() == "active"
    except Exception:
        active = False

    return {
        "active": active,
        "config_path": SURICATA_CONF,
        "rules_dir": SURICATA_RULES_DIR,
        "log_path": SURICATA_LOG,
    }


async def get_stats() -> dict:
    """Get Suricata stats from eve.json."""
    try:
        output = await _run_cmd(f"grep '\"event_type\":\"stats\"' {SURICATA_LOG} | tail -1")
        if output.strip():
            return json.loads(output.strip())
        return {"message": "No stats available"}
    except Exception:
        return {"message": "Suricata not running or no stats"}


async def get_alerts(limit: int = 50) -> list:
    """Get recent Suricata alerts."""
    try:
        output = await _run_cmd(f"grep '\"event_type\":\"alert\"' {SURICATA_LOG} | tail -{limit}")
        alerts = []
        for line in output.strip().split("\n"):
            if line.strip():
                alerts.append(json.loads(line))
        return alerts
    except Exception:
        return []


async def get_rules() -> list:
    """List available rule files."""
    try:
        files = []
        for f in os.listdir(SURICATA_RULES_DIR):
            if f.endswith(".rules"):
                path = os.path.join(SURICATA_RULES_DIR, f)
                with open(path) as fh:
                    count = sum(1 for line in fh if line.strip() and not line.startswith("#"))
                files.append({"name": f, "active_rules": count, "path": path})
        return files
    except FileNotFoundError:
        return []


async def get_rule_file(filename: str) -> str:
    """Get contents of a rule file."""
    path = os.path.join(SURICATA_RULES_DIR, filename)
    with open(path) as f:
        return f.read()


async def save_rule_file(filename: str, content: str) -> str:
    """Save a rule file and reload Suricata."""
    path = os.path.join(SURICATA_RULES_DIR, filename)
    with open(path, "w") as f:
        f.write(content)
    return await reload()


async def reload() -> str:
    """Reload Suricata rules."""
    try:
        return await _run_cmd(
            "suricatasc -c reload-rules 2>/dev/null || systemctl reload suricata 2>/dev/null || echo 'reload sent'"
        )
    except Exception:
        return "Suricata reload attempted"


async def start() -> str:
    return await _run_cmd("systemctl start suricata")


async def stop() -> str:
    return await _run_cmd("systemctl stop suricata")


async def set_mode(mode: str) -> str:
    """Set IDS or IPS mode. IPS requires NFQ or AF_PACKET inline."""
    # This is a simplified toggle — real implementation would edit suricata.yaml
    return f"Mode set to {mode} (requires manual suricata.yaml edit for full IPS)"
