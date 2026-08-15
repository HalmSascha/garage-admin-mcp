"""Shared runtime state (the Garage admin API client, and optionally the S3
object client) for tool modules.

Kept separate from server.py to avoid circular imports: server.py creates
the clients and registers tool modules; tool modules import `get_client`/
`get_s3_client` from here instead of from server.py.
"""

from __future__ import annotations

from .client import GarageAdminClient
from .s3_client import GarageS3Client

_client: GarageAdminClient | None = None
_s3_client: GarageS3Client | None = None


def set_client(client: GarageAdminClient) -> None:
    global _client
    _client = client


def get_client() -> GarageAdminClient:
    if _client is None:
        raise RuntimeError(
            "GarageAdminClient not initialized yet - set_client() must be "
            "called during server startup before any tool runs."
        )
    return _client


def set_s3_client(client: GarageS3Client) -> None:
    global _s3_client
    _s3_client = client


def get_s3_client() -> GarageS3Client:
    if _s3_client is None:
        raise RuntimeError(
            "GarageS3Client not initialized - the S3 object tools require "
            "GARAGE_ADMIN_S3_URL/S3_ACCESS_KEY_ID/S3_SECRET_ACCESS_KEY to "
            "be configured."
        )
    return _s3_client
