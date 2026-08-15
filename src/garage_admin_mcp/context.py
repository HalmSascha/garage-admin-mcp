"""Shared runtime state (the Garage admin API client) for tool modules.

Kept separate from server.py to avoid circular imports: server.py creates
the client and registers tool modules; tool modules import `get_client`
from here instead of from server.py.
"""

from __future__ import annotations

from .client import GarageAdminClient

_client: GarageAdminClient | None = None


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
