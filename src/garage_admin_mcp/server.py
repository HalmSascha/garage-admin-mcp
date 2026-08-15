"""garage-admin-mcp: MCP server for the Garage (deuxfleurs) Admin API.

Exposes Garage's cluster/bucket/key admin operations as MCP tools.
Read-only tools (cluster/bucket/key info) are always registered. Write
tools (create/update/delete buckets and keys, permission changes) are only
registered when GARAGE_ADMIN_READ_ONLY is explicitly set to false - the
default is true, so a fresh deployment is read-only until an operator opts
in. The token used to talk to Garage must independently have the matching
write scopes (see README.md) - the read_only flag only controls which
tools this server *offers*, it is not itself a security boundary.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from .client import GarageAdminClient
from .context import set_client
from .settings import Settings, get_settings
from .tools import buckets, buckets_write, cluster, keys, keys_write, permissions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastMCP:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastMCP) -> AsyncIterator[None]:
        client = GarageAdminClient(
            base_url=settings.url,
            token=settings.token,
            timeout_seconds=settings.request_timeout_seconds,
        )
        set_client(client)
        logger.info("garage-admin-mcp started (read_only=%s, garage_url=%s)", settings.read_only, settings.url)
        try:
            yield
        finally:
            await client.aclose()

    mcp: FastMCP = FastMCP("garage-admin-mcp", lifespan=lifespan)

    cluster.register(mcp)
    buckets.register(mcp)
    keys.register(mcp)

    if not settings.read_only:
        logger.warning(
            "GARAGE_ADMIN_READ_ONLY=false: registering write tools "
            "(bucket/key create-update-delete, permission changes). Make "
            "sure the configured GARAGE_ADMIN_TOKEN actually has the "
            "matching write scopes."
        )
        buckets_write.register(mcp)
        keys_write.register(mcp)
        permissions.register(mcp)

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(_request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    return mcp


def main() -> None:
    settings = get_settings()
    app = create_app(settings)
    app.run(transport="http", host=settings.http_host, port=settings.http_port, path="/mcp")


if __name__ == "__main__":
    main()
