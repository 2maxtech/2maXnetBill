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
