"""garage-admin-mcp: MCP server for the Garage (deuxfleurs) Admin API.

Exposes Garage's cluster/bucket/key admin operations as MCP tools. V1 is
read-only by design (GARAGE_ADMIN_READ_ONLY=true is the default) - write
tools (create/delete buckets and keys, permission changes) are added in a
later phase and gated behind an explicit opt-in once reviewed.
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
from .tools import buckets, cluster, keys

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
        # Write tools land in a later phase (see Plane issue GAMCP-9) - not
        # implemented yet, so read_only=false currently has no extra effect
        # beyond this log line.
        logger.warning(
            "GARAGE_ADMIN_READ_ONLY=false, but write tools are not implemented yet (V1 is read-only only)."
        )

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
