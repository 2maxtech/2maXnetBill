from pydantic import BaseModel


class SetupRequest(BaseModel):
    company_name: str
    admin_username: str
    admin_email: str
    admin_password: str
    router_name: str | None = None
    router_url: str | None = None
    router_username: str = "admin"
    router_password: str = ""


class SetupStatusResponse(BaseModel):
    configured: bool
    deployment_mode: str
