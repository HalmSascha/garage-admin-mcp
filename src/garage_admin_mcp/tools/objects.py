"""Read-only S3 object tools.

Restores the object list/read capability that the previous garage-mcp
(txn2/mcp-s3) provided on NAS01, which this server's Admin-API-only tools
(cluster/buckets/keys/permissions) do not cover.

Only registered when S3 credentials are configured (GARAGE_ADMIN_S3_URL,
GARAGE_ADMIN_S3_ACCESS_KEY_ID, GARAGE_ADMIN_S3_SECRET_ACCESS_KEY) - see
server.py. Deliberately independent of GARAGE_ADMIN_READ_ONLY: these tools
are read-only regardless of that flag, matching the tool they replace
(which ran with MCP_S3_EXT_READONLY=true). Which buckets are actually
reachable is entirely controlled by the S3 credentials' own Garage-side
permissions, not by anything in this server.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import get_s3_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_s3_objects(bucket: str, prefix: str | None = None, max_keys: int = 1000) -> Any:
        """List objects in an S3 bucket via Garage's S3 API (not the admin
        API - use list_buckets/get_bucket_info for bucket-level metadata
        instead). Only buckets the configured S3 credentials have read
        access to are reachable; this call fails for any other bucket.

        Args:
            bucket: Bucket name (e.g. "plane").
            prefix: Only list keys starting with this prefix (like a folder path).
            max_keys: Maximum number of objects to return (default 1000).
        """
        return await get_s3_client().list_objects(bucket, prefix=prefix, max_keys=max_keys)

    @mcp.tool
    async def get_s3_object(bucket: str, key: str, max_bytes: int = 100_000) -> str:
        """Read the text content of an object in an S3 bucket. Only text
        (UTF-8 decodable) objects are supported - binary files raise an
        error rather than returning garbled or base64 output. Content
        longer than max_bytes is truncated with a note appended.

        Args:
            bucket: Bucket name (e.g. "plane").
            key: Object key (path) within the bucket, as returned by list_s3_objects.
            max_bytes: Maximum number of bytes to read (default 100000).
        """
        return await get_s3_client().get_object_text(bucket, key, max_bytes)
