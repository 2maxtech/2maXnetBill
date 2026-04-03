# Gateway + accel-ppp Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy an ISP Gateway LXC with accel-ppp + FreeRADIUS, integrate it with the existing backend via a Gateway Agent API, and validate the full PPPoE lifecycle with a test client.

**Architecture:** ISP Gateway LXC (192.168.40.41) runs accel-ppp for PPPoE, FreeRADIUS for auth/accounting against the App Server's PostgreSQL, and a Gateway Agent (FastAPI on port 8443) that the backend calls to disconnect/throttle/reconnect customers. A test client LXC (192.168.40.42) on an isolated bridge simulates a customer PPPoE router.

**Tech Stack:** accel-ppp, FreeRADIUS 3 (rlm_sql_postgresql), Python 3.12, FastAPI, radclient, Proxmox LXC

**Proxmox host:** 192.168.88.99 (root, `SeafoodCity12#`)
**App Server:** 192.168.40.40 (LXC 108, existing)
**Gateway:** 192.168.40.41 (LXC 111, to create)
**Test Client:** 192.168.40.42 (LXC 112, to create)

---

### Task 1: Proxmox Host Preparation + Create LXCs

All commands run via SSH to root@192.168.88.99.

- [ ] **Step 1: Load PPP kernel modules on Proxmox host**

```bash
ssh root@192.168.88.99 "modprobe ppp_generic && modprobe pppoe && modprobe ppp_async && lsmod | grep ppp"
```

Expected: `ppp_generic`, `pppoe`, `ppp_async` all loaded.

- [ ] **Step 2: Persist kernel modules across reboots**

```bash
ssh root@192.168.88.99 "cat > /etc/modules-load.d/accel-ppp.conf << 'EOF'
ppp_generic
pppoe
ppp_async
EOF"
```

- [ ] **Step 3: Create ISP Gateway LXC (111)**

```bash
ssh root@192.168.88.99 "pct create 111 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname isp-gateway \
  --memory 2048 \
  --swap 1024 \
  --cores 2 \
  --rootfs VMLXC:10 \
  --ostype debian \
  --net0 name=eth0,bridge=vmbr1,tag=40,ip=192.168.40.41/24,gw=192.168.40.1 \
  --net1 name=eth1,bridge=LAN \
  --features nesting=1,keyctl=1 \
  --unprivileged 0 \
  --password SeafoodCity12# \
  --start 1"
```

- [ ] **Step 4: Allow /dev/ppp inside Gateway LXC**

```bash
ssh root@192.168.88.99 "cat >> /etc/pve/lxc/111.conf << 'EOF'
lxc.cgroup2.devices.allow: c 108:0 rwm
lxc.mount.entry: /dev/ppp dev/ppp none bind,create=file
EOF
pct reboot 111"
```

- [ ] **Step 5: Create Test Client LXC (112)**

```bash
ssh root@192.168.88.99 "pct create 112 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname test-client \
  --memory 512 \
  --swap 512 \
  --cores 1 \
  --rootfs VMLXC:4 \
  --ostype debian \
  --net0 name=eth0,bridge=LAN \
  --net1 name=eth1,bridge=vmbr1,tag=40,ip=192.168.40.42/24,gw=192.168.40.1 \
  --features nesting=1 \
  --unprivileged 0 \
  --password SeafoodCity12# \
  --start 1"
```

- [ ] **Step 6: Allow /dev/ppp inside Test Client LXC**

```bash
ssh root@192.168.88.99 "cat >> /etc/pve/lxc/112.conf << 'EOF'
lxc.cgroup2.devices.allow: c 108:0 rwm
lxc.mount.entry: /dev/ppp dev/ppp none bind,create=file
EOF
pct reboot 112"
```

- [ ] **Step 7: Verify both LXCs are running and reachable**

```bash
ssh root@192.168.88.99 "pct list | grep -E '111|112'"
ssh root@192.168.40.41 "hostname && ip addr show eth0 && ip addr show eth1"
ssh root@192.168.40.42 "hostname && ip addr show eth1"
```

Expected: Gateway has eth0 (192.168.40.41) and eth1 (no IP, just link up). Test Client has eth1 (192.168.40.42).

- [ ] **Step 8: Commit plan doc**

```bash
git add docs/superpowers/plans/2026-04-03-gateway-accel-ppp.md
git commit -m "docs: add Gateway + accel-ppp implementation plan"
```

---

### Task 2: PostgreSQL External Access

FreeRADIUS on the Gateway needs to connect to PostgreSQL on the App Server (Docker). Currently PostgreSQL listens on 0.0.0.0:5432 inside Docker (exposed), but pg_hba.conf may reject external connections.

- [ ] **Step 1: Test connectivity from Gateway to App DB**

```bash
ssh root@192.168.40.41 "apt-get update && apt-get install -y postgresql-client && psql -h 192.168.40.40 -U netbill -d netbill -c 'SELECT count(*) FROM customers;'"
```

If this succeeds, pg_hba is already permissive (Docker default allows all). Skip to Step 3.

If it fails with "no pg_hba.conf entry", proceed to Step 2.

- [ ] **Step 2: (Only if Step 1 failed) Add pg_hba entry for Gateway IP**

On the App Server, create a custom pg_hba.conf and mount it into Docker:

```bash
ssh root@192.168.40.40 "mkdir -p /root/2maXnetBill/docker/postgres && cat > /root/2maXnetBill/docker/postgres/pg_hba.conf << 'PGHBA'
# TYPE  DATABASE  USER     ADDRESS             METHOD
local   all       all                          trust
host    all       all      0.0.0.0/0           md5
host    all       all      ::/0                md5
PGHBA"
```

Then update `docker-compose.yml` on local machine to mount it:

Add to the `db` service:
```yaml
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./docker/postgres/pg_hba.conf:/var/lib/postgresql/data/pg_hba.conf
```

Push, pull on App Server, and restart:
```bash
git add docker-compose.yml docker/postgres/pg_hba.conf
git commit -m "feat: allow external PostgreSQL connections for FreeRADIUS"
git push origin main
ssh root@192.168.40.40 "cd /root/2maXnetBill && git pull && docker compose restart db"
```

- [ ] **Step 3: Verify Gateway can query the database**

```bash
ssh root@192.168.40.41 "psql -h 192.168.40.40 -U netbill -d netbill -c \"SELECT pppoe_username, status FROM customers LIMIT 5;\""
```

Expected: Returns customer rows (or empty table).

---

### Task 3: Install accel-ppp on Gateway

- [ ] **Step 1: Install accel-ppp and dependencies**

```bash
ssh root@192.168.40.41 "apt-get update && apt-get install -y accel-ppp accel-ppp-modules"
```

If `accel-ppp` is not in Debian 12 repos, build from source:

```bash
ssh root@192.168.40.41 "apt-get update && apt-get install -y \
  build-essential cmake gcc linux-headers-\$(uname -r) \
  libpcre3-dev libssl-dev liblua5.1-0-dev git && \
  cd /usr/src && \
  git clone https://github.com/accel-ppp/accel-ppp.git && \
  mkdir accel-ppp/build && cd accel-ppp/build && \
  cmake -DBUILD_PPTP_DRIVER=FALSE \
        -DBUILD_IPOE_DRIVER=FALSE \
        -DRADIUS=TRUE \
        -DSHAPER=TRUE \
        -DLOG_PGSQL=FALSE \
        -DCMAKE_INSTALL_PREFIX=/usr \
        -DKDIR=/lib/modules/\$(uname -r)/build \
        .. && \
  make -j\$(nproc) && make install"
```

- [ ] **Step 2: Create accel-ppp configuration**

```bash
ssh root@192.168.40.41 "mkdir -p /var/log/accel-ppp && cat > /etc/accel-ppp.conf << 'CONF'
[modules]
log_file
pppoe
auth_radius
radius
shaper
ippool

[core]
log-error=/var/log/accel-ppp/core.log
thread-count=2

[common]

[ppp]
verbose=1
min-mtu=1280
mtu=1492
mru=1492
ipv4=require
lcp-echo-interval=30
lcp-echo-failure=3

[pppoe]
interface=eth1
verbose=1
padi-limit=0

[dns]
dns1=8.8.8.8
dns2=8.8.4.4

[radius]
dictionary=/usr/share/accel-ppp/radius/dictionary
nas-identifier=2maXnetBill-GW
nas-ip-address=192.168.40.41
server=127.0.0.1,testing123,auth-port=1812,acct-port=1813,req-limit=0,fail-time=0
dae-server=127.0.0.1:3799,testing123
acct-timeout=3
acct-delay-time=0
acct-on=0
verbose=1

[ip-pool]
gw=10.0.0.1
10.0.0.2-254,name=main

[shaper]
attr=WISPr-Bandwidth-Max-Down
attr-down=WISPr-Bandwidth-Max-Down
attr-up=WISPr-Bandwidth-Max-Up
verbose=1

[log]
log-file=/var/log/accel-ppp/accel-ppp.log
log-emerg=/var/log/accel-ppp/emerg.log
log-fail-file=/var/log/accel-ppp/auth-fail.log
level=3
copy=1

[cli]
telnet=127.0.0.1:2001
history-file=/var/log/accel-ppp/cli-history

[connlimit]
limit=10/min
burst=3
timeout=60
CONF"
```

- [ ] **Step 3: Create accel-ppp systemd service**

```bash
ssh root@192.168.40.41 "cat > /etc/systemd/system/accel-ppp.service << 'SVC'
[Unit]
Description=accel-ppp PPPoE Server
After=network.target

[Service]
Type=forking
ExecStart=/usr/sbin/accel-pppd -d -c /etc/accel-ppp.conf -p /var/run/accel-ppp.pid
ExecReload=/bin/kill -HUP \$MAINPID
PIDFile=/var/run/accel-ppp.pid
Restart=on-failure

[Install]
WantedBy=multi-user.target
SVC
systemctl daemon-reload && systemctl enable accel-ppp"
```

- [ ] **Step 4: Do NOT start accel-ppp yet** — FreeRADIUS needs to be configured first. We'll start both together in Task 5.

---

### Task 4: Install and Configure FreeRADIUS

- [ ] **Step 1: Install FreeRADIUS with PostgreSQL module**

```bash
ssh root@192.168.40.41 "apt-get install -y freeradius freeradius-postgresql freeradius-utils"
```

- [ ] **Step 2: Enable SQL module and PostgreSQL driver**

```bash
ssh root@192.168.40.41 "cd /etc/freeradius/3.0/mods-enabled && ln -sf ../mods-available/sql sql"
```

- [ ] **Step 3: Configure SQL module for PostgreSQL**

```bash
ssh root@192.168.40.41 "cat > /etc/freeradius/3.0/mods-available/sql << 'SQLMOD'
sql {
    driver = \"rlm_sql_postgresql\"
    dialect = \"postgresql\"

    server = \"192.168.40.40\"
    port = 5432
    login = \"netbill\"
    password = \"netbill\"

    radius_db = \"netbill\"

    acct_table1 = \"pppoe_sessions\"
    acct_table2 = \"pppoe_sessions\"
    authcheck_table = \"customers\"
    authreply_table = \"customers\"
    groupcheck_table = \"customers\"
    groupreply_table = \"customers\"

    read_clients = no
    delete_stale_sessions = yes

    pool {
        start = 5
        min = 3
        max = 10
        spare = 3
        uses = 0
        lifetime = 0
        idle_timeout = 60
    }

    # Custom queries
    authorize_check_query = \"SELECT pppoe_password AS 'cleartext-password' FROM customers WHERE pppoe_username = '%{User-Name}' AND status NOT IN ('disconnected', 'terminated')\"

    authorize_reply_query = \"SELECT 'WISPr-Bandwidth-Max-Down' AS attribute, CASE WHEN c.status = 'suspended' THEN '1000000' ELSE (p.download_mbps * 1000000)::text END AS value, ':=' AS op FROM customers c JOIN plans p ON c.plan_id = p.id WHERE c.pppoe_username = '%{User-Name}' UNION ALL SELECT 'WISPr-Bandwidth-Max-Up', CASE WHEN c.status = 'suspended' THEN '512000' ELSE (p.upload_mbps * 1000000)::text END, ':=' FROM customers c JOIN plans p ON c.plan_id = p.id WHERE c.pppoe_username = '%{User-Name}' UNION ALL SELECT 'Framed-Pool', 'main', ':='\"

    authorize_group_check_query = \"\"
    authorize_group_reply_query = \"\"

    accounting_onoff_query = \"\"

    accounting_Start_query = \"INSERT INTO pppoe_sessions (id, customer_id, session_id, ip_address, mac_address, started_at, bytes_in, bytes_out, created_at) SELECT gen_random_uuid(), c.id, '%{Acct-Session-Id}', '%{Framed-IP-Address}', '%{Calling-Station-Id}', NOW(), 0, 0, NOW() FROM customers c WHERE c.pppoe_username = '%{User-Name}'\"

    accounting_Interim_query = \"UPDATE pppoe_sessions SET bytes_in = '%{Acct-Input-Octets}'::bigint, bytes_out = '%{Acct-Output-Octets}'::bigint WHERE session_id = '%{Acct-Session-Id}' AND ended_at IS NULL\"

    accounting_Stop_query = \"UPDATE pppoe_sessions SET bytes_in = '%{Acct-Input-Octets}'::bigint, bytes_out = '%{Acct-Output-Octets}'::bigint, ended_at = NOW(), disconnect_reason = '%{Acct-Terminate-Cause}' WHERE session_id = '%{Acct-Session-Id}' AND ended_at IS NULL\"
}
SQLMOD"
```

- [ ] **Step 4: Add SQL to the default site authorize and accounting sections**

```bash
ssh root@192.168.40.41 "cp /etc/freeradius/3.0/sites-available/default /etc/freeradius/3.0/sites-available/default.bak"
```

Edit the default site to include `sql` in the authorize and accounting sections:

```bash
ssh root@192.168.40.41 "sed -i '/^authorize {/,/^}/ { /files/a\\        sql' /etc/freeradius/3.0/sites-available/default }
sed -i '/^accounting {/,/^}/ { /detail/a\\        sql' /etc/freeradius/3.0/sites-available/default }"
```

Alternatively, replace the key sections more reliably:

```bash
ssh root@192.168.40.41 "cat > /etc/freeradius/3.0/sites-available/default << 'SITE'
server default {

listen {
    type = auth
    ipaddr = *
    port = 0
}

listen {
    type = acct
    ipaddr = *
    port = 0
}

authorize {
    preprocess
    sql
    pap
}

authenticate {
    Auth-Type PAP {
        pap
    }
}

preacct {
    preprocess
    acct_unique
}

accounting {
    sql
}

session {
    sql
}

post-auth {
}

}
SITE"
```

- [ ] **Step 5: Configure RADIUS clients (accel-ppp)**

```bash
ssh root@192.168.40.41 "cat > /etc/freeradius/3.0/clients.conf << 'CLIENTS'
client localhost {
    ipaddr = 127.0.0.1
    secret = testing123
    nastype = other
    shortname = accel-ppp
}
CLIENTS"
```

- [ ] **Step 6: Add WISPr dictionary attributes**

```bash
ssh root@192.168.40.41 "cat >> /etc/freeradius/3.0/dictionary << 'DICT'

\$INCLUDE /usr/share/freeradius/dictionary.wispr
DICT"
```

- [ ] **Step 7: Test FreeRADIUS configuration (dry run)**

```bash
ssh root@192.168.40.41 "freeradius -XC 2>&1 | tail -5"
```

Expected: `Configuration appears to be OK` (or similar success message).

---

### Task 5: Start Services + First PPPoE Test

- [ ] **Step 1: Ensure a test customer exists in the database**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && docker compose exec db psql -U netbill -d netbill -c \"
  INSERT INTO plans (id, name, download_mbps, upload_mbps, monthly_price, is_active, created_at)
  SELECT gen_random_uuid(), 'Test 10Mbps', 10, 5, 999.00, true, NOW()
  WHERE NOT EXISTS (SELECT 1 FROM plans WHERE name = 'Test 10Mbps');
  
  INSERT INTO customers (id, full_name, email, phone, pppoe_username, pppoe_password, status, plan_id, created_at)
  SELECT gen_random_uuid(), 'Test User', 'test@test.com', '09170000000', 'testuser', 'testpass123', 'active',
    (SELECT id FROM plans WHERE name = 'Test 10Mbps' LIMIT 1), NOW()
  WHERE NOT EXISTS (SELECT 1 FROM customers WHERE pppoe_username = 'testuser');
\""
```

- [ ] **Step 2: Start FreeRADIUS in debug mode**

```bash
ssh root@192.168.40.41 "systemctl stop freeradius; freeradius -X &"
```

- [ ] **Step 3: Test RADIUS authentication**

```bash
ssh root@192.168.40.41 "echo 'User-Name = testuser, User-Password = testpass123' | radtest testuser testpass123 127.0.0.1 0 testing123"
```

Expected: `Access-Accept` with WISPr-Bandwidth-Max-Down and WISPr-Bandwidth-Max-Up attributes.

If it fails, check the debug output from Step 2 for SQL errors.

- [ ] **Step 4: Stop debug FreeRADIUS, start both services properly**

```bash
ssh root@192.168.40.41 "pkill freeradius; systemctl start freeradius && systemctl start accel-ppp && sleep 2 && systemctl status freeradius --no-pager && systemctl status accel-ppp --no-pager"
```

Expected: Both services active and running.

- [ ] **Step 5: Verify accel-ppp is listening on eth1**

```bash
ssh root@192.168.40.41 "accel-cmd show stat"
```

Expected: Shows accel-ppp statistics (sessions: 0, etc.).

---

### Task 6: Test Client Setup + PPPoE Connection

- [ ] **Step 1: Install PPPoE client on test client LXC**

```bash
ssh root@192.168.40.42 "apt-get update && apt-get install -y pppoe pppoeconf ppp"
```

- [ ] **Step 2: Configure PPPoE client**

```bash
ssh root@192.168.40.42 "cat > /etc/ppp/peers/2maxnet << 'PEER'
plugin rp-pppoe.so eth0
user \"testuser\"
password \"testpass123\"
noauth
defaultroute
persist
maxfail 3
holdoff 10
lcp-echo-interval 30
lcp-echo-failure 3
mtu 1492
mru 1492
PEER

cat > /etc/ppp/chap-secrets << 'CHAP'
\"testuser\" * \"testpass123\" *
CHAP

cat > /etc/ppp/pap-secrets << 'PAP'
\"testuser\" * \"testpass123\" *
PAP

chmod 600 /etc/ppp/chap-secrets /etc/ppp/pap-secrets"
```

- [ ] **Step 3: Dial PPPoE**

```bash
ssh root@192.168.40.42 "pon 2maxnet && sleep 5 && ip addr show ppp0"
```

Expected: `ppp0` interface with IP address from 10.0.0.x range.

- [ ] **Step 4: Verify session on Gateway**

```bash
ssh root@192.168.40.41 "accel-cmd show sessions"
```

Expected: Shows one active session for `testuser` with assigned IP.

- [ ] **Step 5: Verify session recorded in database**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && docker compose exec db psql -U netbill -d netbill -c \"SELECT session_id, ip_address, mac_address, started_at, bytes_in, bytes_out FROM pppoe_sessions WHERE ended_at IS NULL;\""
```

Expected: One active session row.

- [ ] **Step 6: Verify RADIUS accounting writes traffic data**

Wait 30+ seconds for an interim accounting update, then:

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && docker compose exec db psql -U netbill -d netbill -c \"SELECT bytes_in, bytes_out FROM pppoe_sessions WHERE ended_at IS NULL;\""
```

Expected: `bytes_in` / `bytes_out` values have updated from 0.

- [ ] **Step 7: Disconnect test client**

```bash
ssh root@192.168.40.42 "poff 2maxnet && sleep 2 && ip addr show ppp0 2>&1"
```

Expected: ppp0 no longer exists.

- [ ] **Step 8: Verify session ended in database**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && docker compose exec db psql -U netbill -d netbill -c \"SELECT session_id, ended_at, disconnect_reason FROM pppoe_sessions ORDER BY started_at DESC LIMIT 1;\""
```

Expected: `ended_at` is populated, `disconnect_reason` shows the termination cause.

---

### Task 7: Gateway Agent (FastAPI)

**Files to create on the Gateway LXC (192.168.40.41):**
- `/opt/gateway-agent/requirements.txt`
- `/opt/gateway-agent/agent/__init__.py`
- `/opt/gateway-agent/agent/main.py`
- `/opt/gateway-agent/agent/core/__init__.py`
- `/opt/gateway-agent/agent/core/config.py`
- `/opt/gateway-agent/agent/core/security.py`
- `/opt/gateway-agent/agent/services/__init__.py`
- `/opt/gateway-agent/agent/services/accel_ppp.py`
- `/opt/gateway-agent/agent/api/__init__.py`
- `/opt/gateway-agent/agent/api/pppoe.py`
- `/opt/gateway-agent/agent/api/system.py`
- `/etc/systemd/system/gateway-agent.service`

Also create in local repo (for version control):
- `gateway-agent/` (mirror of the above)

- [ ] **Step 1: Install Python on Gateway**

```bash
ssh root@192.168.40.41 "apt-get install -y python3 python3-pip python3-venv"
```

- [ ] **Step 2: Create Gateway Agent project structure**

Create locally in the repo first, then deploy to the Gateway.

Create `gateway-agent/requirements.txt`:

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
psutil==6.1.1
```

Create `gateway-agent/agent/__init__.py` (empty).

Create `gateway-agent/agent/core/__init__.py` (empty).

Create `gateway-agent/agent/core/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: str = "change-me-in-production"
    ACCEL_CLI_HOST: str = "127.0.0.1"
    ACCEL_CLI_PORT: int = 2001
    RADIUS_SECRET: str = "testing123"
    RADIUS_SERVER: str = "127.0.0.1"
    RADIUS_COA_PORT: int = 3799
    NAS_IP: str = "192.168.40.41"

    class Config:
        env_file = "/opt/gateway-agent/.env"


settings = Settings()
```

Create `gateway-agent/agent/core/security.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from agent.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key
```

Create `gateway-agent/agent/services/__init__.py` (empty).

Create `gateway-agent/agent/services/accel_ppp.py`:

```python
import asyncio
import subprocess


async def accel_cmd(command: str) -> str:
    """Execute a command via accel-ppp telnet CLI."""
    proc = await asyncio.create_subprocess_exec(
        "accel-cmd", command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"accel-cmd failed: {stderr.decode()}")
    return stdout.decode()


async def get_sessions() -> list[dict]:
    """Get all active PPPoE sessions from accel-ppp."""
    output = await accel_cmd("show sessions")
    sessions = []
    lines = output.strip().split("\n")
    if len(lines) < 2:
        return sessions

    # Parse header to get column positions
    header = lines[0]
    columns = header.split("|")
    col_names = [c.strip().lower() for c in columns]

    for line in lines[1:]:
        if line.startswith("-") or not line.strip():
            continue
        values = line.split("|")
        if len(values) != len(col_names):
            continue
        row = {col_names[i]: values[i].strip() for i in range(len(col_names))}
        sessions.append(row)

    return sessions


async def find_session_by_username(username: str) -> dict | None:
    """Find an active session by PPPoE username."""
    sessions = await get_sessions()
    for s in sessions:
        if s.get("username") == username:
            return s
    return None


def send_radius_packet(packet_type: str, attributes: dict, secret: str, server: str, port: int) -> str:
    """Send a RADIUS CoA or Disconnect packet using radclient."""
    attr_lines = "\n".join(f"{k} = {v}" for k, v in attributes.items())
    result = subprocess.run(
        ["radclient", "-x", f"{server}:{port}", packet_type, secret],
        input=attr_lines,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"radclient failed: {result.stderr}")
    return result.stdout
```

Create `gateway-agent/agent/api/__init__.py` (empty).

Create `gateway-agent/agent/api/pppoe.py`:

```python
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
    # Reconnect is passive — customer status is already updated in DB.
    # FreeRADIUS will allow the next auth attempt.
    # Customer router auto-redials.
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
```

Create `gateway-agent/agent/api/system.py`:

```python
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
```

Create `gateway-agent/agent/main.py`:

```python
from fastapi import FastAPI

from agent.api.pppoe import router as pppoe_router
from agent.api.system import router as system_router

app = FastAPI(title="2maXnetBill Gateway Agent")

app.include_router(pppoe_router)
app.include_router(system_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway-agent"}
```

- [ ] **Step 3: Deploy Gateway Agent to LXC**

```bash
# Copy files to Gateway
scp -r gateway-agent/* root@192.168.40.41:/opt/gateway-agent/

# Install dependencies
ssh root@192.168.40.41 "cd /opt/gateway-agent && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt && ./venv/bin/pip install pydantic-settings"
```

- [ ] **Step 4: Create .env file on Gateway**

```bash
ssh root@192.168.40.41 "cat > /opt/gateway-agent/.env << 'ENV'
API_KEY=dev-gateway-key-2maxnet
ENV"
```

- [ ] **Step 5: Create systemd service for Gateway Agent**

```bash
ssh root@192.168.40.41 "cat > /etc/systemd/system/gateway-agent.service << 'SVC'
[Unit]
Description=2maXnetBill Gateway Agent
After=network.target accel-ppp.service

[Service]
Type=simple
WorkingDirectory=/opt/gateway-agent
ExecStart=/opt/gateway-agent/venv/bin/uvicorn agent.main:app --host 192.168.40.41 --port 8443
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC
systemctl daemon-reload && systemctl enable gateway-agent && systemctl start gateway-agent"
```

- [ ] **Step 6: Verify Gateway Agent is running**

```bash
ssh root@192.168.40.41 "curl -s http://192.168.40.41:8443/health"
```

Expected: `{"status":"ok","service":"gateway-agent"}`

- [ ] **Step 7: Test session listing via Gateway Agent**

First, connect the test client:
```bash
ssh root@192.168.40.42 "pon 2maxnet && sleep 5"
```

Then query:
```bash
ssh root@192.168.40.41 "curl -s -H 'X-API-Key: dev-gateway-key-2maxnet' http://192.168.40.41:8443/agent/pppoe/sessions"
```

Expected: JSON array with the active test session.

- [ ] **Step 8: Test disconnect via Gateway Agent**

```bash
ssh root@192.168.40.41 "curl -s -X POST http://192.168.40.41:8443/agent/pppoe/disconnect \
  -H 'X-API-Key: dev-gateway-key-2maxnet' \
  -H 'Content-Type: application/json' \
  -d '{\"customer_id\":\"test\",\"pppoe_username\":\"testuser\"}'"
```

Expected: `{"status":"disconnected","detail":"..."}` and test client loses PPPoE connection.

- [ ] **Step 9: Commit Gateway Agent code**

```bash
git add gateway-agent/
git commit -m "feat: Gateway Agent with PPPoE disconnect/throttle/sessions endpoints"
```

---

### Task 8: Backend Integration — Gateway Service + PPPoE API

**Files to create:**
- `backend/app/services/__init__.py`
- `backend/app/services/gateway.py`
- `backend/app/api/admin/pppoe.py`

**Files to modify:**
- `backend/app/api/admin/customers.py` (add disconnect/reconnect/throttle endpoints)
- `backend/app/main.py` (register pppoe router)
- `backend/app/core/config.py` (update GATEWAY_AGENT_URL)

- [ ] **Step 1: Create gateway service**

Create `backend/app/services/__init__.py` (empty).

Create `backend/app/services/gateway.py`:

```python
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(10.0)
HEADERS = {"X-API-Key": settings.GATEWAY_API_KEY}


async def _request(method: str, path: str, json: dict | None = None) -> dict:
    url = f"{settings.GATEWAY_AGENT_URL}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT, verify=False) as client:
        response = await client.request(method, url, headers=HEADERS, json=json)
        response.raise_for_status()
        return response.json()


async def get_active_sessions() -> list[dict]:
    return await _request("GET", "/agent/pppoe/sessions")


async def disconnect_customer(customer_id: str, pppoe_username: str) -> dict:
    return await _request("POST", "/agent/pppoe/disconnect", json={
        "customer_id": customer_id,
        "pppoe_username": pppoe_username,
    })


async def reconnect_customer(customer_id: str, pppoe_username: str) -> dict:
    return await _request("POST", "/agent/pppoe/reconnect", json={
        "customer_id": customer_id,
        "pppoe_username": pppoe_username,
    })


async def throttle_customer(customer_id: str, pppoe_username: str, download_mbps: int, upload_kbps: int) -> dict:
    return await _request("POST", "/agent/pppoe/throttle", json={
        "customer_id": customer_id,
        "pppoe_username": pppoe_username,
        "download_mbps": download_mbps,
        "upload_kbps": upload_kbps,
    })
```

- [ ] **Step 2: Create PPPoE session API endpoints**

Create `backend/app/api/admin/pppoe.py`:

```python
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.pppoe_session import PPPoESession
from app.models.user import User
from app.services import gateway

router = APIRouter(prefix="/pppoe", tags=["pppoe"])


@router.get("/sessions")
async def list_active_sessions(
    current_user: User = Depends(get_current_user),
):
    try:
        sessions = await gateway.get_active_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gateway unreachable: {str(e)}")


@router.delete("/sessions/{session_id}")
async def kill_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PPPoESession).where(PPPoESession.session_id == session_id, PPPoESession.ended_at.is_(None))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Look up customer username for the disconnect
        from app.models.customer import Customer
        cust_result = await db.execute(select(Customer).where(Customer.id == session.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        response = await gateway.disconnect_customer(str(customer.id), customer.pppoe_username)
        return {"status": "killed", "detail": response}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)}")
```

- [ ] **Step 3: Add disconnect/reconnect/throttle to customers API**

Add these endpoints to `backend/app/api/admin/customers.py` (append after the existing delete endpoint):

```python
from app.models.disconnect_log import DisconnectAction, DisconnectLog, DisconnectReason
from app.services import gateway
from datetime import datetime, timezone


@router.post("/{customer_id}/disconnect", status_code=200)
async def disconnect_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        response = await gateway.disconnect_customer(str(customer.id), customer.pppoe_username)
    except Exception:
        response = {"detail": "Gateway unreachable, session may still be active"}

    customer.status = CustomerStatus.disconnected
    log = DisconnectLog(
        customer_id=customer.id,
        action=DisconnectAction.disconnect,
        reason=DisconnectReason.manual,
        performed_by=current_user.id,
        performed_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    return {"status": "disconnected", "gateway_response": response}


@router.post("/{customer_id}/reconnect", status_code=200)
async def reconnect_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        response = await gateway.reconnect_customer(str(customer.id), customer.pppoe_username)
    except Exception:
        response = {"detail": "Gateway unreachable"}

    customer.status = CustomerStatus.active
    log = DisconnectLog(
        customer_id=customer.id,
        action=DisconnectAction.reconnect,
        reason=DisconnectReason.manual,
        performed_by=current_user.id,
        performed_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    return {"status": "reconnected", "gateway_response": response}


@router.post("/{customer_id}/throttle", status_code=200)
async def throttle_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    from app.core.config import settings
    try:
        response = await gateway.throttle_customer(
            str(customer.id), customer.pppoe_username,
            settings.THROTTLE_DOWNLOAD_MBPS, settings.THROTTLE_UPLOAD_KBPS,
        )
    except Exception:
        response = {"detail": "Gateway unreachable"}

    customer.status = CustomerStatus.suspended
    log = DisconnectLog(
        customer_id=customer.id,
        action=DisconnectAction.throttle,
        reason=DisconnectReason.manual,
        performed_by=current_user.id,
        performed_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    return {"status": "throttled", "gateway_response": response}
```

- [ ] **Step 4: Register PPPoE router in main.py**

Add to `backend/app/main.py`:

```python
from app.api.admin.pppoe import router as pppoe_router

app.include_router(pppoe_router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 5: Update GATEWAY_AGENT_URL in config and docker-compose**

Update `docker-compose.dev.yml` to set the Gateway Agent URL:

```yaml
services:
  backend:
    environment:
      SECRET_KEY: dev-secret-key-not-for-production
      GATEWAY_API_KEY: dev-gateway-key-2maxnet
      GATEWAY_AGENT_URL: http://192.168.40.41:8443
```

- [ ] **Step 6: Commit backend changes**

```bash
git add backend/app/services/ backend/app/api/admin/pppoe.py backend/app/api/admin/customers.py backend/app/main.py docker-compose.dev.yml
git commit -m "feat: backend Gateway service + PPPoE session + customer action endpoints"
```

- [ ] **Step 7: Deploy updated backend to App Server**

```bash
git push origin main
ssh root@192.168.40.40 "cd /root/2maXnetBill && git pull && docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d && sleep 5 && curl -s http://localhost:8000/health"
```

---

### Task 9: End-to-End Smoke Test

- [ ] **Step 1: Connect test client PPPoE**

```bash
ssh root@192.168.40.42 "pon 2maxnet && sleep 5 && ip addr show ppp0"
```

Expected: ppp0 with 10.0.0.x IP.

- [ ] **Step 2: Verify session via backend API**

```bash
TOKEN=$(ssh root@192.168.40.40 "curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"access_token\"])'")

ssh root@192.168.40.40 "curl -s http://localhost:8000/api/v1/pppoe/sessions -H 'Authorization: Bearer $TOKEN'"
```

Expected: JSON with the active PPPoE session.

- [ ] **Step 3: Test throttle via backend API**

Get the test customer ID:
```bash
CUST_ID=$(ssh root@192.168.40.40 "curl -s 'http://localhost:8000/api/v1/customers/?search=testuser' -H 'Authorization: Bearer $TOKEN' | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"items\"][0][\"id\"])'")

ssh root@192.168.40.40 "curl -s -X POST http://localhost:8000/api/v1/customers/$CUST_ID/throttle -H 'Authorization: Bearer $TOKEN'"
```

Expected: `{"status":"throttled",...}`. Customer status changes to `suspended`.

- [ ] **Step 4: Test disconnect via backend API**

```bash
ssh root@192.168.40.40 "curl -s -X POST http://localhost:8000/api/v1/customers/$CUST_ID/disconnect -H 'Authorization: Bearer $TOKEN'"
```

Expected: `{"status":"disconnected",...}`. Test client loses PPPoE.

Verify on test client:
```bash
ssh root@192.168.40.42 "ip addr show ppp0 2>&1"
```

Expected: `Device "ppp0" does not exist.`

- [ ] **Step 5: Test reconnect via backend API**

```bash
ssh root@192.168.40.40 "curl -s -X POST http://localhost:8000/api/v1/customers/$CUST_ID/reconnect -H 'Authorization: Bearer $TOKEN'"
```

Then redial on test client:
```bash
ssh root@192.168.40.42 "pon 2maxnet && sleep 5 && ip addr show ppp0"
```

Expected: ppp0 back online with IP from pool.

- [ ] **Step 6: Verify disconnect log in database**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && docker compose exec db psql -U netbill -d netbill -c 'SELECT action, reason, performed_at FROM disconnect_logs ORDER BY performed_at DESC LIMIT 5;'"
```

Expected: throttle, disconnect, reconnect entries.

- [ ] **Step 7: Test auth rejection for disconnected customer**

```bash
# Set customer to disconnected
ssh root@192.168.40.40 "curl -s -X POST http://localhost:8000/api/v1/customers/$CUST_ID/disconnect -H 'Authorization: Bearer $TOKEN'"

# Try to connect — should fail
ssh root@192.168.40.42 "poff 2maxnet 2>/dev/null; pon 2maxnet && sleep 8 && ip addr show ppp0 2>&1"
```

Expected: ppp0 does not exist — FreeRADIUS rejects auth for `disconnected` status.

- [ ] **Step 8: Reconnect and verify full restore**

```bash
ssh root@192.168.40.40 "curl -s -X POST http://localhost:8000/api/v1/customers/$CUST_ID/reconnect -H 'Authorization: Bearer $TOKEN'"
ssh root@192.168.40.42 "poff 2maxnet 2>/dev/null; pon 2maxnet && sleep 5 && ip addr show ppp0"
```

Expected: Back online at full speed.

- [ ] **Step 9: Final commit**

```bash
git push origin main
```
