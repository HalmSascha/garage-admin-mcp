"""Configuration for garage-admin-mcp, sourced from environment variables."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    All values are read from environment variables (optionally via a .env
    file during local development). See README.md for the full list.
    """

    model_config = SettingsConfigDict(env_prefix="GARAGE_ADMIN_", env_file=".env", extra="ignore")

    url: str = Field(
        description="Base URL of the Garage admin API, e.g. http://192.0.2.10:3903",
    )
    token: str = Field(
        description=(
            "Bearer token for the Garage admin API. Should be a scoped "
            "admin-token created via `garage admin-token create`, not the "
            "static master admin_token from garage.toml."
        ),
    )
    read_only: bool = Field(
        default=True,
        description=(
            "When true (default), only read-only tools are registered. "
            "Set to false to additionally register write tools (bucket/key "
            "creation, deletion, permission changes) once the server has "
            "been reviewed and the underlying token has write scopes."
        ),
    )
    http_host: str = Field(default="0.0.0.0", description="Host to bind the MCP HTTP transport to.")
    http_port: int = Field(default=8000, description="Port to bind the MCP HTTP transport to.")
    request_timeout_seconds: float = Field(
        default=10.0, description="Timeout for requests to the Garage admin API."
    )


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from env
