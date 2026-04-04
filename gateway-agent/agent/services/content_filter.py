import asyncio
import logging
import os

logger = logging.getLogger(__name__)

BLOCKLIST_DIR = "/etc/dnsmasq.d"
DNS_BLOCKLIST = f"{BLOCKLIST_DIR}/netbill-blocklist.conf"
GEOIP_BLOCKLIST = "/etc/nftables.d/geoip-block.nft"


async def _run_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{stderr.decode()}")
    return stdout.decode()


# --- DNS Filtering ---

async def get_dns_blocklist() -> str:
    """Get current DNS blocklist."""
    try:
        with open(DNS_BLOCKLIST) as f:
            return f.read()
    except FileNotFoundError:
        return ""


async def apply_dns_blocklist(domains: list[str]) -> str:
    """Apply DNS blocklist — blocks domains by pointing them to 0.0.0.0."""
    lines = [f"address=/{d}/0.0.0.0" for d in domains if d.strip()]
    with open(DNS_BLOCKLIST, "w") as f:
        f.write("\n".join(lines) + "\n")
    return await _run_cmd("systemctl reload dnsmasq 2>/dev/null || systemctl restart dnsmasq")


async def add_blocked_domain(domain: str) -> str:
    """Add a single domain to blocklist."""
    entry = f"address=/{domain}/0.0.0.0\n"
    with open(DNS_BLOCKLIST, "a") as f:
        f.write(entry)
    return await _run_cmd("systemctl reload dnsmasq 2>/dev/null || systemctl restart dnsmasq")


async def remove_blocked_domain(domain: str) -> str:
    """Remove a domain from blocklist."""
    try:
        with open(DNS_BLOCKLIST) as f:
            lines = f.readlines()
        with open(DNS_BLOCKLIST, "w") as f:
            for line in lines:
                if f"/{domain}/" not in line:
                    f.write(line)
        return await _run_cmd("systemctl reload dnsmasq 2>/dev/null || systemctl restart dnsmasq")
    except FileNotFoundError:
        return "No blocklist file"


async def get_blocked_domains() -> list:
    """Parse and return list of blocked domains."""
    try:
        with open(DNS_BLOCKLIST) as f:
            domains = []
            for line in f:
                line = line.strip()
                if line.startswith("address=/"):
                    parts = line.split("/")
                    if len(parts) >= 3:
                        domains.append(parts[1])
            return domains
    except FileNotFoundError:
        return []


# --- GeoIP Blocking ---

async def get_geoip_config() -> str:
    """Get GeoIP blocking config."""
    try:
        with open(GEOIP_BLOCKLIST) as f:
            return f.read()
    except FileNotFoundError:
        return ""


async def apply_geoip_block(country_codes: list[str]) -> str:
    """Apply GeoIP blocking via nftables sets. Requires nftables geoip module."""
    rules = [
        "#!/usr/sbin/nft -f",
        "",
        "table inet geoip_filter {",
        "  chain input {",
        "    type filter hook input priority -1; policy accept;",
    ]

    for cc in country_codes:
        rules.append(f"    # Block {cc.upper()}")
        rules.append(f"    ip saddr @geoip_{cc.lower()} drop")

    rules.extend(["  }", "}", ""])

    content = "\n".join(rules)
    with open(GEOIP_BLOCKLIST, "w") as f:
        f.write(content)

    try:
        return await _run_cmd(f"nft -f {GEOIP_BLOCKLIST}")
    except Exception as e:
        return f"GeoIP rules written but apply failed (geoip module may not be installed): {e}"


async def get_blocked_countries() -> list:
    """Get list of blocked country codes."""
    try:
        with open(GEOIP_BLOCKLIST) as f:
            countries = []
            for line in f:
                if "geoip_" in line and "drop" in line:
                    # Extract country code from @geoip_XX
                    parts = line.split("geoip_")
                    if len(parts) >= 2:
                        cc = parts[1].split()[0].upper()
                        countries.append(cc)
            return countries
    except FileNotFoundError:
        return []
