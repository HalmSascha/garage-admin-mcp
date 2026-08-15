"""Thin, read-only wrapper around Garage's S3 API (not the Admin API).

This exists specifically to restore the object list/read capability that
the previous garage-mcp (txn2/mcp-s3) provided on NAS01, which the rest of
this server's Admin-API-only tools do not cover (Admin API manages buckets/
keys/permissions; it has no notion of the objects stored inside a bucket).

Deliberately read-only and independent of GARAGE_ADMIN_READ_ONLY: object
writes were never in scope even in the tool this replaces (it ran with
MCP_S3_EXT_READONLY=true). If write support is ever needed, it should be a
conscious, separately-reviewed addition - not a side effect of flipping the
admin read-only flag.
"""

from __future__ import annotations

import asyncio
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class S3ObjectError(RuntimeError):
    """Raised when the underlying S3 call fails."""


class GarageS3Client:
    """Synchronous boto3 S3 client, called via asyncio.to_thread so it fits
    the rest of this server's async tool interface without pulling in a
    second async HTTP stack just for this."""

    def __init__(
        self, endpoint_url: str | None, access_key_id: str, secret_access_key: str, region: str = "garage"
    ) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=Config(s3={"addressing_style": "path"}),
        )

    async def list_objects(
        self, bucket: str, *, prefix: str | None = None, max_keys: int = 1000
    ) -> list[dict[str, Any]]:
        def _call() -> list[dict[str, Any]]:
            kwargs: dict[str, Any] = {"Bucket": bucket, "MaxKeys": max_keys}
            if prefix:
                kwargs["Prefix"] = prefix
            try:
                response = self._client.list_objects_v2(**kwargs)
            except ClientError as exc:
                raise S3ObjectError(str(exc)) from exc
            return [
                {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                }
                for obj in response.get("Contents", [])
            ]

        return await asyncio.to_thread(_call)

    async def get_object_text(self, bucket: str, key: str, max_bytes: int) -> str:
        def _call() -> str:
            try:
                response = self._client.get_object(Bucket=bucket, Key=key)
                body = response["Body"].read(max_bytes + 1)
            except ClientError as exc:
                raise S3ObjectError(str(exc)) from exc
            truncated = len(body) > max_bytes
            body = body[:max_bytes]
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise S3ObjectError(
                    f"Object {key!r} in bucket {bucket!r} is not valid UTF-8 text "
                    "(binary file?) - this tool only supports reading text objects."
                ) from exc
            if truncated:
                text += f"\n\n[... truncated, object exceeds {max_bytes} bytes ...]"
            return text

        return await asyncio.to_thread(_call)
