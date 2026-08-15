"""Write tools for S3 access keys.

Only registered when GARAGE_ADMIN_READ_ONLY=false (see server.py).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def create_key(name: str | None = None) -> Any:
        """Create a new S3 access key. The response includes the new key's
        secret access key in cleartext exactly once - Garage never returns
        it again after this call, so make sure the caller captures it. The
        new key starts with no bucket permissions; use allow_bucket_key to
        grant access to specific buckets.

        Args:
            name: Optional display name for the key.
        """
        return await get_client().create_key(name=name)

    @mcp.tool
    async def update_key(id: str, name: str | None = None, never_expires: bool | None = None) -> Any:
        """Rename a key and/or clear its expiration date. Only the
        arguments you pass are changed.

        Args:
            id: The key's Garage-internal ID (as returned by list_keys).
            name: New display name for the key.
            never_expires: Pass true to remove any expiration date from the key.
        """
        return await get_client().update_key(id, name=name, never_expires=never_expires)

    @mcp.tool
    async def delete_key(id: str, confirm_id: str) -> Any:
        """Permanently delete an S3 access key, revoking all its access
        immediately. THIS CANNOT BE UNDONE.

        To prevent an LLM from deleting the wrong key based on an ambiguous
        instruction, confirm_id is required and must be byte-for-byte
        identical to id - the call is rejected locally, before any request
        reaches Garage, if they don't match.

        Args:
            id: The key's Garage-internal ID (as returned by list_keys).
            confirm_id: Must equal id exactly.
        """
        if confirm_id != id:
            raise ValueError(
                f"confirm_id ({confirm_id!r}) does not match id ({id!r}) - "
                "refusing to delete. Pass the exact key id in both "
                "arguments to confirm."
            )
        return await get_client().delete_key(id)

    @mcp.tool
    async def import_key(access_key_id: str, secret_access_key: str, name: str | None = None) -> Any:
        """Register an existing S3 access key pair (e.g. one generated
        outside Garage's admin API) with the cluster, so it can be granted
        bucket permissions like any other key.

        Security note: this tool's arguments include a real credential
        (secret_access_key). Only import keys you already control. The
        secret is sent to Garage as part of this call; be aware that it
        will also appear in this MCP call's arguments/conversation history
        wherever that is logged or stored by the client.

        Args:
            access_key_id: The access key ID to import.
            secret_access_key: The matching secret access key.
            name: Optional display name for the key.
        """
        return await get_client().import_key(access_key_id, secret_access_key, name=name)
