"""Read-only access-key tools.

Security note: the underlying GetKeyInfo endpoint supports a
`showSecretKey` parameter that returns the S3 secret access key in
cleartext. That parameter is deliberately NOT exposed here - an MCP tool
that an LLM can call from natural-language conversation is not a safe place
to surface raw credentials. get_key_info always requests the key info
without the secret.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_keys() -> Any:
        """List all S3 access keys registered in the Garage cluster, with
        their IDs and names (no secrets). Use get_key_info for full detail
        on one key, including which buckets it can access."""
        return await get_client().list_keys()

    @mcp.tool
    async def get_key_info(id: str | None = None, search: str | None = None) -> Any:
        """Get full detail on a single S3 access key: its name, which
        buckets it has read/write/owner permissions on, and quotas. Never
        returns the secret access key value (deliberately not exposed by
        this tool, see module docstring).

        Exactly one of the arguments should normally be given.

        Args:
            id: The key's Garage-internal ID (as returned by list_keys).
            search: Free-text search across key IDs and names; matches a
                single key unambiguously or returns an error listing the
                ambiguous candidates.
        """
        return await get_client().get_key_info(id=id, search=search, show_secret_key=False)
