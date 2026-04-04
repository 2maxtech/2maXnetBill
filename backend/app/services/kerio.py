import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class KerioClient:
    """Kerio Control JSON-RPC API client."""

    def __init__(self):
        self.url = f"{settings.KERIO_URL}/admin/api/jsonrpc"
        self.token: str | None = None
        self.client: httpx.AsyncClient | None = None
        self._request_id = 0

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(verify=False, timeout=30.0)
        return self.client

    async def _rpc(self, method: str, params: dict | None = None, retry: bool = True) -> Any:
        """Make a JSON-RPC call to Kerio Control."""
        self._request_id += 1
        body = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }

        client = await self._get_client()
        headers = {"Content-Type": "application/json-rpc"}
        if self.token:
            headers["X-Token"] = self.token

        response = await client.post(self.url, json=body, headers=headers)
        data = response.json()

        if "error" in data:
            error = data["error"]
            # Session expired — re-login and retry
            if error.get("code") == -32001 and retry:
                logger.info("Kerio session expired, re-authenticating")
                await self.login()
                return await self._rpc(method, params, retry=False)
            raise KerioError(error.get("message", "Unknown error"), error.get("code", 0))

        return data.get("result")

    async def login(self) -> bool:
        """Authenticate with Kerio Control."""
        result = await self._rpc("Session.login", {
            "userName": settings.KERIO_ADMIN_USER,
            "password": settings.KERIO_ADMIN_PASSWORD,
            "application": {
                "name": "2maXnetBill",
                "vendor": "2maXnet",
                "version": "1.0",
            },
        }, retry=False)
        self.token = result.get("token")
        logger.info("Kerio Control authenticated")
        return True

    async def logout(self) -> None:
        """End session."""
        try:
            await self._rpc("Session.logout", retry=False)
        except Exception:
            pass
        self.token = None

    # --- Users ---

    async def get_users(self, limit: int = 200) -> list[dict]:
        """Get all local users."""
        result = await self._rpc("Users.get", {
            "query": {
                "start": 0,
                "limit": limit,
                "orderBy": [{"columnName": "loginName", "direction": "Asc"}],
            },
            "domainId": settings.KERIO_DOMAIN_ID,
        })
        return result.get("list", [])

    async def get_user(self, user_id: str) -> dict | None:
        """Get a specific user by Kerio ID."""
        users = await self.get_users()
        for u in users:
            if u.get("id") == user_id:
                return u
        return None

    async def create_user(self, username: str, password: str, full_name: str, mac: str | None = None) -> str:
        """Create a local Kerio user. Returns the user ID."""
        user = {
            "credentials": {
                "userName": username,
                "password": password,
                "passwordChanged": True,
            },
            "fullName": full_name,
            "description": "2maXnetBill subscriber",
            "authType": "Internal",
            "localEnabled": True,
            "useTemplate": True,
            "autoLogin": {
                "macAddresses": {
                    "enabled": bool(mac),
                    "value": [mac] if mac else [],
                },
                "addresses": {"enabled": False, "value": []},
                "addressGroup": {"enabled": False, "id": "", "name": ""},
            },
        }

        result = await self._rpc("Users.create", {
            "users": [user],
            "domainId": settings.KERIO_DOMAIN_ID,
        })

        errors = result.get("errors", [])
        if errors:
            raise KerioError(f"Failed to create user: {errors}")

        # Get the created user's ID
        created_ids = result.get("createdIds", [])
        if created_ids:
            return created_ids[0]

        # Fallback: find by username
        users = await self.get_users()
        for u in users:
            if u.get("credentials", {}).get("userName") == username:
                return u["id"]

        raise KerioError("User created but ID not found")

    async def update_user(self, user_id: str, fields: dict) -> None:
        """Update user fields."""
        user = await self.get_user(user_id)
        if not user:
            raise KerioError(f"User {user_id} not found")

        user.update(fields)
        await self._rpc("Users.set", {
            "userIds": [user_id],
            "details": fields,
        })

    async def enable_user(self, user_id: str) -> None:
        """Enable a user (reconnect after payment)."""
        await self._rpc("Users.set", {
            "userIds": [user_id],
            "details": {"localEnabled": True},
        })
        logger.info(f"Kerio user {user_id} enabled")

    async def disable_user(self, user_id: str) -> None:
        """Disable a user (graduated disconnect)."""
        await self._rpc("Users.set", {
            "userIds": [user_id],
            "details": {"localEnabled": False},
        })
        logger.info(f"Kerio user {user_id} disabled")

    async def delete_user(self, user_id: str) -> None:
        """Delete a user."""
        await self._rpc("Users.remove", {
            "userIds": [user_id],
        })
        logger.info(f"Kerio user {user_id} deleted")

    async def set_mac_binding(self, user_id: str, mac_addresses: list[str]) -> None:
        """Set MAC address auto-login for a user."""
        await self._rpc("Users.set", {
            "userIds": [user_id],
            "details": {
                "autoLogin": {
                    "macAddresses": {
                        "enabled": bool(mac_addresses),
                        "value": mac_addresses,
                    },
                    "addresses": {"enabled": False, "value": []},
                    "addressGroup": {"enabled": False, "id": "", "name": ""},
                },
            },
        })
        logger.info(f"Kerio user {user_id} MAC binding set: {mac_addresses}")

    # --- Active Hosts ---

    async def get_active_hosts(self, limit: int = 200) -> list[dict]:
        """Get currently connected hosts."""
        result = await self._rpc("ActiveHosts.get", {
            "query": {
                "start": 0,
                "limit": limit,
                "orderBy": [],
            },
        })
        return result.get("list", [])

    # --- Bandwidth ---

    async def get_bandwidth_rules(self) -> dict:
        """Get bandwidth management config."""
        return await self._rpc("BandwidthManagement.get", {})

    async def set_bandwidth_rules(self, config: dict) -> None:
        """Set bandwidth management config."""
        await self._rpc("BandwidthManagement.set", {"config": config})

    # --- Traffic Policy ---

    async def get_traffic_policies(self) -> list[dict]:
        """Get traffic policy rules."""
        result = await self._rpc("TrafficPolicy.get", {})
        return result.get("list", [])

    # --- Status ---

    async def get_interfaces(self) -> list[dict]:
        """Get network interfaces."""
        result = await self._rpc("Interfaces.get", {
            "query": {
                "start": 0,
                "limit": 50,
                "orderBy": [],
            },
        })
        return result.get("list", [])


class KerioError(Exception):
    """Kerio Control API error."""
    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(message)


# Singleton instance
kerio = KerioClient()
