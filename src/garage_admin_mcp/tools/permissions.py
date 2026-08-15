"""Bucket <-> key permission tools.

Only registered when GARAGE_ADMIN_READ_ONLY=false (see server.py).

Garage's own admin API docs carry an explicit disclaimer that
AllowBucketKey/DenyBucketKey have "an unconventional semantic": each call
only touches the permission flags explicitly set to true, leaving all other
flags (including the ones on the *other* endpoint) unchanged. There is no
"set exactly these permissions" call - the two tools below intentionally
mirror that additive/subtractive behaviour instead of hiding it, since
papering over it would make the tools lie about what they did.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def allow_bucket_key(
        bucket_id: str,
        access_key_id: str,
        read: bool = False,
        write: bool = False,
        owner: bool = False,
    ) -> Any:
        """Grant a key permissions on a bucket.

        Garage's own semantics (not a simplification made here): only the
        flags you set to true are granted. Flags left false are NOT
        revoked - they simply keep whatever permission they already had.
        This call can only add permissions; use deny_bucket_key to remove
        one.

        Args:
            bucket_id: The bucket's Garage-internal ID.
            access_key_id: The key's Garage-internal ID.
            read: Grant read (GetObject/ListObjects) access.
            write: Grant write (PutObject/DeleteObject) access.
            owner: Grant owner access (bucket management, e.g. quotas/website).
        """
        return await get_client().allow_bucket_key(
            bucket_id, access_key_id, read=read, write=write, owner=owner
        )

    @mcp.tool
    async def deny_bucket_key(
        bucket_id: str,
        access_key_id: str,
        read: bool = False,
        write: bool = False,
        owner: bool = False,
    ) -> Any:
        """Revoke a key's permissions on a bucket.

        Garage's own semantics (not a simplification made here): only the
        flags you set to true are revoked. Flags left false are NOT
        granted - they simply keep whatever permission they already had.
        This call can only remove permissions; use allow_bucket_key to add
        one.

        Args:
            bucket_id: The bucket's Garage-internal ID.
            access_key_id: The key's Garage-internal ID.
            read: Revoke read access.
            write: Revoke write access.
            owner: Revoke owner access.
        """
        return await get_client().deny_bucket_key(
            bucket_id, access_key_id, read=read, write=write, owner=owner
        )
