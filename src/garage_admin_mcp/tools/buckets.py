"""Read-only bucket tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_buckets() -> Any:
        """List all buckets in the Garage cluster, with their IDs, global/
        local aliases, and a few key flags (e.g. whether a website is
        configured). Use get_bucket_info for full detail on one bucket."""
        return await get_client().list_buckets()

    @mcp.tool
    async def get_bucket_info(
        id: str | None = None,
        global_alias: str | None = None,
        search: str | None = None,
    ) -> Any:
        """Get full detail on a single bucket: aliases, website
        configuration, quotas, storage usage, object count, and which keys
        have which permissions on it.

        Exactly one of the arguments should normally be given.

        Args:
            id: The bucket's Garage-internal ID (as returned by list_buckets).
            global_alias: The bucket's global alias/name, e.g. "plane".
            search: Free-text search across bucket IDs and aliases; matches
                a single bucket unambiguously or returns an error listing
                the ambiguous candidates.
        """
        return await get_client().get_bucket_info(id=id, global_alias=global_alias, search=search)
