# WireGuard VPN Auto-Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let tenants set up a WireGuard VPN tunnel to their MikroTik router through a simple two-step UI flow: paste a generated script into MikroTik, paste the resulting public key back into NetLedger.

**Architecture:** Add `wg_tunnel_ip` and `wg_peer_public_key` columns to the `routers` table. A lightweight WG management HTTP API runs on the host LXC (where WireGuard lives) at `localhost:9999`, called by the backend container at `192.168.40.40:9999`. The frontend Routers page gets a "Setup VPN" button that opens a two-step wizard modal.

**Tech Stack:** Python (http.server for host API), FastAPI (backend endpoints), Vue 3 + Tailwind (frontend modal), Alembic (migration), systemd (host service)

---

## File Structure

### New Files
- `backend/alembic/versions/008_wireguard_fields.py` — Migration adding WG fields to routers
- `backend/app/api/admin/vpn.py` — VPN setup/activate/status endpoints
- `/opt/netledger/wg-api.py` — Host-side WG management HTTP API (deployed to LXC, not in repo)

### Modified Files
- `backend/app/models/router.py` — Add `wg_tunnel_ip`, `wg_peer_public_key` fields
- `backend/app/schemas/router.py` — Add WG fields to response schema
- `backend/app/main.py` — Register VPN router
- `frontend/src/api/routers.ts` — Add VPN API functions
- `frontend/src/pages/Routers.vue` — Add VPN setup button + wizard modal

---

### Task 1: Database Migration

**Files:**
- Create: `backend/alembic/versions/008_wireguard_fields.py`
- Modify: `backend/app/models/router.py`
- Modify: `backend/app/schemas/router.py`

- [ ] **Step 1: Create migration file**

```python
# backend/alembic/versions/008_wireguard_fields.py
"""add wireguard tunnel fields to routers

Revision ID: 008_wireguard
Revises: 007_multi_tenant
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = '008_wireguard'
down_revision = '007_multi_tenant'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('routers', sa.Column('wg_tunnel_ip', sa.String(45), nullable=True))
    op.add_column('routers', sa.Column('wg_peer_public_key', sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column('routers', 'wg_peer_public_key')
    op.drop_column('routers', 'wg_tunnel_ip')
```

- [ ] **Step 2: Add fields to Router model**

In `backend/app/models/router.py`, add after `maintenance_message`:

```python
wg_tunnel_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
wg_peer_public_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
```

- [ ] **Step 3: Add fields to Router schemas**

In `backend/app/schemas/router.py`, add to `RouterResponse`:

```python
wg_tunnel_ip: str | None = None
wg_peer_public_key: str | None = None
```

- [ ] **Step 4: Run migration on server**

```bash
ssh root@192.168.40.40 "docker compose -f /root/2maXnetBill/docker-compose.yml exec -T backend alembic upgrade head"
```

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/008_wireguard_fields.py backend/app/models/router.py backend/app/schemas/router.py
git commit -m "feat: add wireguard tunnel fields to routers table"
```

---

### Task 2: Host WireGuard Management API

**Files:**
- Create: `/opt/netledger/wg-api.py` (on host LXC 192.168.40.40)
- Create: systemd service file

- [ ] **Step 1: Create the WG management script on the host**

```python
#!/usr/bin/env python3
"""Minimal HTTP API for managing WireGuard peers. Runs on the host LXC."""
import json
import subprocess
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

WG_INTERFACE = "wg0"
SERVER_PUBLIC_KEY = ""  # Filled on startup
SERVER_ENDPOINT = "24.78.94.166:443"


def _run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def get_server_public_key():
    r = _run(f"wg show {WG_INTERFACE} public-key")
    return r.stdout.strip()


def get_next_tunnel_ip():
    """Find next available 10.10.10.x IP."""
    r = _run(f"wg show {WG_INTERFACE} allowed-ips")
    used = set()
    for line in r.stdout.strip().split("\n"):
        for m in re.findall(r"10\.10\.10\.(\d+)", line):
            used.add(int(m))
    # 1 is server, start from 2
    for i in range(2, 255):
        if i not in used:
            return f"10.10.10.{i}"
    return None


def add_peer(public_key, tunnel_ip, client_lan=""):
    allowed = f"{tunnel_ip}/32"
    if client_lan:
        allowed += f",{client_lan}"
    r = _run(f"wg set {WG_INTERFACE} peer '{public_key}' allowed-ips '{allowed}' persistent-keepalive 25")
    if r.returncode != 0:
        return False, r.stderr
    _run(f"wg-quick save {WG_INTERFACE}")
    return True, "ok"


def remove_peer(public_key):
    r = _run(f"wg set {WG_INTERFACE} peer '{public_key}' remove")
    _run(f"wg-quick save {WG_INTERFACE}")
    return r.returncode == 0


def get_peer_status(public_key):
    r = _run(f"wg show {WG_INTERFACE} dump")
    for line in r.stdout.strip().split("\n")[1:]:  # Skip interface line
        parts = line.split("\t")
        if len(parts) >= 5 and parts[0] == public_key:
            return {
                "public_key": parts[0],
                "endpoint": parts[2] if parts[2] != "(none)" else None,
                "latest_handshake": int(parts[4]) if parts[4] != "0" else 0,
                "rx_bytes": int(parts[5]),
                "tx_bytes": int(parts[6]),
            }
    return None


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        if self.path == "/info":
            self._json(200, {
                "server_public_key": SERVER_PUBLIC_KEY,
                "endpoint": SERVER_ENDPOINT,
            })
        elif self.path.startswith("/status/"):
            key = self.path[8:]
            status = get_peer_status(key)
            self._json(200, status or {"error": "peer not found"})
        elif self.path == "/next-ip":
            ip = get_next_tunnel_ip()
            self._json(200, {"tunnel_ip": ip})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        body = self._read_body()
        if self.path == "/add-peer":
            ok, msg = add_peer(body["public_key"], body["tunnel_ip"], body.get("client_lan", ""))
            self._json(200 if ok else 500, {"ok": ok, "message": msg})
        elif self.path == "/remove-peer":
            ok = remove_peer(body["public_key"])
            self._json(200, {"ok": ok})
        else:
            self._json(404, {"error": "not found"})

    def log_message(self, format, *args):
        pass  # Suppress logs


if __name__ == "__main__":
    SERVER_PUBLIC_KEY = get_server_public_key()
    print(f"WG API starting. Server key: {SERVER_PUBLIC_KEY}")
    HTTPServer(("0.0.0.0", 9999), Handler).serve_forever()
```

- [ ] **Step 2: Deploy script and create systemd service on host**

```bash
ssh root@192.168.40.40 "mkdir -p /opt/netledger"
# Copy script to host (use scp or cat)
ssh root@192.168.40.40 "cat > /etc/systemd/system/wg-api.service << 'EOF'
[Unit]
Description=NetLedger WireGuard Management API
After=network.target wg-quick@wg0.service

[Service]
ExecStart=/usr/bin/python3 /opt/netledger/wg-api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable wg-api && systemctl start wg-api"
```

- [ ] **Step 3: Verify the API works**

```bash
ssh root@192.168.40.40 "curl -s http://localhost:9999/info"
# Should return: {"server_public_key":"eagJdY+...","endpoint":"24.78.94.166:443"}
ssh root@192.168.40.40 "curl -s http://localhost:9999/next-ip"
# Should return: {"tunnel_ip":"10.10.10.3"} (2 is taken by bar23me)
```

- [ ] **Step 4: Commit** (no repo files for this task — host-only deployment)

---

### Task 3: Backend VPN Endpoints

**Files:**
- Create: `backend/app/api/admin/vpn.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create VPN API router**

```python
# backend/app/api/admin/vpn.py
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.tenant import get_tenant_id
from app.models.router import Router
from app.models.user import User

router = APIRouter(prefix="/vpn", tags=["vpn"])

WG_API_URL = "http://192.168.40.40:9999"


class VpnActivateRequest(BaseModel):
    public_key: str
    client_lan: str = ""


async def _wg_api(method: str, path: str, json: dict | None = None) -> dict:
    """Call the host WireGuard management API."""
    async with httpx.AsyncClient(timeout=10) as client:
        if method == "GET":
            r = await client.get(f"{WG_API_URL}{path}")
        else:
            r = await client.post(f"{WG_API_URL}{path}", json=json)
        return r.json()


@router.post("/{router_id}/setup")
async def vpn_setup(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_tenant_id),
):
    """Generate WireGuard setup script for a router. Returns MikroTik commands."""
    tid = uuid.UUID(tenant_id)
    result = await db.execute(select(Router).where(Router.id == router_id, Router.owner_id == tid))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")

    # Get server info and next available IP
    try:
        info = await _wg_api("GET", "/info")
        ip_data = await _wg_api("GET", "/next-ip")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VPN service unavailable: {e}")

    tunnel_ip = r.wg_tunnel_ip or ip_data["tunnel_ip"]
    server_key = info["server_public_key"]
    endpoint = info["endpoint"]

    # Save assigned tunnel IP
    if not r.wg_tunnel_ip:
        r.wg_tunnel_ip = tunnel_ip
        await db.flush()

    # Generate MikroTik script
    script = (
        f'/interface/wireguard/add name=wg-netledger listen-port=13231\n'
        f'/interface/wireguard/peers/add interface=wg-netledger '
        f'public-key="{server_key}" '
        f'endpoint-address={endpoint.split(":")[0]} '
        f'endpoint-port={endpoint.split(":")[1]} '
        f'allowed-address=10.10.10.0/24 '
        f'persistent-keepalive=25\n'
        f'/ip/address/add address={tunnel_ip}/24 interface=wg-netledger'
    )

    return {
        "tunnel_ip": tunnel_ip,
        "server_public_key": server_key,
        "endpoint": endpoint,
        "script": script,
        "instructions": [
            "1. Open your MikroTik terminal (Winbox Terminal tab or SSH)",
            "2. Paste the script below and press Enter",
            "3. Run:  /interface/wireguard/print",
            "4. Copy the Public Key shown and paste it back here",
        ],
    }


@router.post("/{router_id}/activate")
async def vpn_activate(
    router_id: uuid.UUID,
    body: VpnActivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_tenant_id),
):
    """Activate VPN tunnel by adding tenant's public key as a WireGuard peer."""
    tid = uuid.UUID(tenant_id)
    result = await db.execute(select(Router).where(Router.id == router_id, Router.owner_id == tid))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")

    if not r.wg_tunnel_ip:
        raise HTTPException(status_code=400, detail="Run VPN setup first")

    # Add peer to WireGuard
    try:
        resp = await _wg_api("POST", "/add-peer", {
            "public_key": body.public_key,
            "tunnel_ip": r.wg_tunnel_ip,
            "client_lan": body.client_lan,
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VPN service error: {e}")

    if not resp.get("ok"):
        raise HTTPException(status_code=500, detail=resp.get("message", "Failed to add peer"))

    # Save public key and update router URL to tunnel IP
    r.wg_peer_public_key = body.public_key
    r.url = f"http://{r.wg_tunnel_ip}"
    await db.flush()

    # Invalidate cached MikroTik client so it picks up new URL
    from app.services.mikrotik import invalidate_client
    invalidate_client(str(router_id))

    return {
        "status": "activated",
        "tunnel_ip": r.wg_tunnel_ip,
        "router_url": r.url,
        "message": "VPN tunnel activated. Router URL updated to tunnel IP.",
    }


@router.get("/{router_id}/vpn-status")
async def vpn_status(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Check VPN tunnel status for a router."""
    tid = uuid.UUID(tenant_id)
    result = await db.execute(select(Router).where(Router.id == router_id, Router.owner_id == tid))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")

    if not r.wg_peer_public_key:
        return {"status": "not_configured", "tunnel_ip": r.wg_tunnel_ip}

    try:
        peer = await _wg_api("GET", f"/status/{r.wg_peer_public_key}")
    except Exception:
        return {"status": "service_unavailable"}

    if peer.get("error"):
        return {"status": "peer_not_found", "tunnel_ip": r.wg_tunnel_ip}

    connected = peer.get("latest_handshake", 0) > 0
    return {
        "status": "connected" if connected else "waiting",
        "tunnel_ip": r.wg_tunnel_ip,
        "endpoint": peer.get("endpoint"),
        "latest_handshake": peer.get("latest_handshake"),
        "rx_bytes": peer.get("rx_bytes", 0),
        "tx_bytes": peer.get("tx_bytes", 0),
    }
```

- [ ] **Step 2: Register VPN router in main.py**

In `backend/app/main.py`, add the import and include:

```python
from app.api.admin.vpn import router as vpn_router
app.include_router(vpn_router, prefix="/api/v1")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/admin/vpn.py backend/app/main.py
git commit -m "feat: add VPN setup/activate/status API endpoints"
```

---

### Task 4: Frontend API Functions

**Files:**
- Modify: `frontend/src/api/routers.ts`

- [ ] **Step 1: Add VPN API functions**

Add to the end of `frontend/src/api/routers.ts`:

```typescript
// VPN
export interface VpnSetupResponse {
  tunnel_ip: string
  server_public_key: string
  endpoint: string
  script: string
  instructions: string[]
}

export interface VpnActivateResponse {
  status: string
  tunnel_ip: string
  router_url: string
  message: string
}

export interface VpnStatusResponse {
  status: string
  tunnel_ip?: string
  endpoint?: string
  latest_handshake?: number
  rx_bytes?: number
  tx_bytes?: number
}

export function vpnSetup(routerId: string) {
  return api.post<VpnSetupResponse>(`/vpn/${routerId}/setup`)
}

export function vpnActivate(routerId: string, data: { public_key: string; client_lan?: string }) {
  return api.post<VpnActivateResponse>(`/vpn/${routerId}/activate`, data)
}

export function vpnStatus(routerId: string) {
  return api.get<VpnStatusResponse>(`/vpn/${routerId}/vpn-status`)
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/routers.ts
git commit -m "feat: add VPN API client functions"
```

---

### Task 5: Frontend VPN Setup Wizard

**Files:**
- Modify: `frontend/src/pages/Routers.vue`

- [ ] **Step 1: Add imports and state**

In the `<script setup>` section, add to the imports from `'../api/routers'`:

```typescript
import {
  // ... existing imports ...
  vpnSetup,
  vpnActivate,
  vpnStatus,
  type VpnSetupResponse,
} from '../api/routers'
```

Add state variables after the existing scan modal state:

```typescript
// VPN Setup
const showVpnModal = ref(false)
const vpnStep = ref<1 | 2 | 3>(1)
const vpnLoading = ref(false)
const vpnRouterId = ref('')
const vpnRouterName = ref('')
const vpnData = ref<VpnSetupResponse | null>(null)
const vpnClientKey = ref('')
const vpnClientLan = ref('')
const vpnError = ref('')
const vpnSuccess = ref('')
const vpnCopied = ref(false)

async function startVpnSetup(router: RouterType) {
  vpnRouterId.value = router.id
  vpnRouterName.value = router.name
  vpnStep.value = 1
  vpnData.value = null
  vpnClientKey.value = ''
  vpnClientLan.value = ''
  vpnError.value = ''
  vpnSuccess.value = ''
  vpnCopied.value = false
  showVpnModal.value = true
  vpnLoading.value = true
  try {
    const { data } = await vpnSetup(router.id)
    vpnData.value = data
  } catch (e: any) {
    vpnError.value = e.response?.data?.detail || 'Failed to generate VPN setup'
  } finally {
    vpnLoading.value = false
  }
}

function copyVpnScript() {
  if (vpnData.value?.script) {
    navigator.clipboard.writeText(vpnData.value.script)
    vpnCopied.value = true
    setTimeout(() => vpnCopied.value = false, 2000)
  }
}

async function activateVpn() {
  if (!vpnClientKey.value.trim()) {
    vpnError.value = 'Please paste your MikroTik public key'
    return
  }
  vpnError.value = ''
  vpnLoading.value = true
  try {
    const { data } = await vpnActivate(vpnRouterId.value, {
      public_key: vpnClientKey.value.trim(),
      client_lan: vpnClientLan.value.trim(),
    })
    vpnSuccess.value = data.message
    vpnStep.value = 3
    await loadRouters()
  } catch (e: any) {
    vpnError.value = e.response?.data?.detail || 'Failed to activate VPN'
  } finally {
    vpnLoading.value = false
  }
}
```

- [ ] **Step 2: Add VPN button to router actions**

In the template, find the actions cell and add the VPN button after "Import":

```html
<button @click="startVpnSetup(r)" class="text-xs font-medium text-purple-600 hover:text-purple-700 transition-colors">VPN</button>
```

- [ ] **Step 3: Add VPN Setup Modal**

Add before the closing `</div>` of the template (before Confirm Delete):

```html
<!-- VPN Setup Modal -->
<Modal :open="showVpnModal" :title="'VPN Setup — ' + vpnRouterName" size="lg" @close="showVpnModal = false">
  <div class="space-y-4">
    <!-- Steps indicator -->
    <div class="flex items-center gap-2 text-xs font-medium">
      <span :class="vpnStep >= 1 ? 'text-primary' : 'text-gray-400'">1. Copy Script</span>
      <svg class="w-4 h-4 text-gray-300" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd"/></svg>
      <span :class="vpnStep >= 2 ? 'text-primary' : 'text-gray-400'">2. Enter Key</span>
      <svg class="w-4 h-4 text-gray-300" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd"/></svg>
      <span :class="vpnStep >= 3 ? 'text-primary' : 'text-gray-400'">3. Connected</span>
    </div>

    <!-- Loading -->
    <div v-if="vpnLoading && !vpnData" class="flex items-center justify-center py-8">
      <svg class="w-8 h-8 animate-spin text-primary" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
    </div>

    <!-- Step 1: Copy Script -->
    <div v-if="vpnStep === 1 && vpnData">
      <p class="text-sm text-gray-600 mb-3">
        Paste this script into your MikroTik terminal (Winbox Terminal tab or SSH):
      </p>
      <div class="relative rounded-xl bg-gray-900 p-4 overflow-x-auto">
        <pre class="text-sm text-green-400 font-mono whitespace-pre">{{ vpnData.script }}</pre>
        <button
          @click="copyVpnScript"
          class="absolute top-2 right-2 px-2.5 py-1 text-xs rounded-lg transition-colors"
          :class="vpnCopied ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        >
          {{ vpnCopied ? 'Copied!' : 'Copy' }}
        </button>
      </div>
      <div class="mt-3 rounded-lg bg-blue-50 border border-blue-200 p-3">
        <p class="text-sm text-blue-700">
          After pasting, run <code class="bg-blue-100 px-1 rounded">/interface/wireguard/print</code> and copy the <strong>Public Key</strong> shown.
        </p>
      </div>
    </div>

    <!-- Step 2: Enter Public Key -->
    <div v-if="vpnStep === 2">
      <p class="text-sm text-gray-600 mb-3">
        Paste the <strong>Public Key</strong> from your MikroTik WireGuard interface:
      </p>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">MikroTik Public Key</label>
        <input
          v-model="vpnClientKey"
          type="text"
          placeholder="e.g. VSs6joEGtYn6ZQJJiqSepzR+H3xK82f37H1EqUUeE2k="
          class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
        />
      </div>
      <div class="mt-3">
        <label class="block text-sm font-medium text-gray-700 mb-1.5">
          Router LAN Subnet <span class="text-gray-400 font-normal">(optional — e.g. 192.168.1.0/24)</span>
        </label>
        <input
          v-model="vpnClientLan"
          type="text"
          placeholder="192.168.1.0/24"
          class="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
        />
      </div>
    </div>

    <!-- Step 3: Connected -->
    <div v-if="vpnStep === 3">
      <div class="rounded-lg bg-green-50 border border-green-200 p-4 text-center">
        <svg class="w-12 h-12 text-green-500 mx-auto mb-2" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>
        <p class="text-lg font-semibold text-green-800">VPN Tunnel Activated!</p>
        <p class="text-sm text-green-700 mt-1">{{ vpnSuccess }}</p>
        <p class="text-sm text-gray-600 mt-2">Your router URL has been updated to <code class="bg-green-100 px-1.5 py-0.5 rounded font-mono text-green-800">http://{{ vpnData?.tunnel_ip }}</code></p>
      </div>
    </div>

    <!-- Error -->
    <div v-if="vpnError" class="rounded-lg bg-red-50 border border-red-200 p-3">
      <p class="text-sm text-red-700">{{ vpnError }}</p>
    </div>
  </div>

  <template #footer>
    <button @click="showVpnModal = false" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
      {{ vpnStep === 3 ? 'Done' : 'Cancel' }}
    </button>
    <button
      v-if="vpnStep === 1 && vpnData"
      @click="vpnStep = 2; vpnError = ''"
      class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover"
    >
      Next — I've pasted the script
    </button>
    <button
      v-if="vpnStep === 2"
      @click="activateVpn"
      :disabled="vpnLoading || !vpnClientKey.trim()"
      class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-hover disabled:opacity-50"
    >
      {{ vpnLoading ? 'Activating...' : 'Activate VPN' }}
    </button>
  </template>
</Modal>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/routers.ts frontend/src/pages/Routers.vue
git commit -m "feat: VPN setup wizard on Routers page"
```

---

### Task 6: Deploy and Test

- [ ] **Step 1: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Deploy to server**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && git pull origin main && docker compose up -d --build"
```

- [ ] **Step 3: Run migration**

```bash
ssh root@192.168.40.40 "docker compose -f /root/2maXnetBill/docker-compose.yml exec -T backend alembic upgrade head"
```

- [ ] **Step 4: Verify WG API is running**

```bash
ssh root@192.168.40.40 "curl -s http://localhost:9999/info"
```

- [ ] **Step 5: Test the full flow via UI**

1. Login as super admin, impersonate a tenant
2. Go to Routers page, click VPN on a router
3. Verify script is generated with correct server key and endpoint
4. Verify the two-step wizard works

- [ ] **Step 6: Final commit with any fixes**
