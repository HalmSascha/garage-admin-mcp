"""Thin async client for the Garage (deuxfleurs) Admin API v2.

Reference: https://garagehq.deuxfleurs.fr/api/garage-admin-v2.json
"""

from __future__ import annotations

from typing import Any, Self

import httpx


class GarageAdminError(RuntimeError):
    """Raised when the Garage admin API returns an error response."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Garage admin API error {status_code}: {body!r}")


class GarageAdminClient:
    """Minimal async wrapper around the Garage Admin API v2.

    Every method maps 1:1 to a `GET /v2/<OperationId>` endpoint and returns
    the parsed JSON body as-is (a dict or list), so that new fields Garage
    adds in future releases pass through without requiring a client update.
    """

    def __init__(self, base_url: str, token: str, timeout_seconds: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout_seconds,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        response = await self._client.get(path, params=params)
        if response.status_code >= 400:
            try:
                body: Any = response.json()
            except ValueError:
                body = response.text
            raise GarageAdminError(response.status_code, body)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    # -- Cluster -----------------------------------------------------------

    async def get_cluster_status(self) -> Any:
        return await self._get("/v2/GetClusterStatus")

    async def get_cluster_health(self) -> Any:
        return await self._get("/v2/GetClusterHealth")

    async def get_cluster_statistics(self) -> Any:
        return await self._get("/v2/GetClusterStatistics")

    async def get_cluster_layout(self) -> Any:
        return await self._get("/v2/GetClusterLayout")

    async def get_node_info(self, node: str) -> Any:
        return await self._get("/v2/GetNodeInfo", {"node": node})

    async def get_node_statistics(self, node: str) -> Any:
        return await self._get("/v2/GetNodeStatistics", {"node": node})

    # -- Buckets -------------------------------------------------------------

    async def list_buckets(self) -> Any:
        return await self._get("/v2/ListBuckets")

    async def get_bucket_info(
        self,
        *,
        id: str | None = None,
        global_alias: str | None = None,
        search: str | None = None,
    ) -> Any:
        return await self._get(
            "/v2/GetBucketInfo",
            {"id": id, "globalAlias": global_alias, "search": search},
        )

    # -- Keys ------------------------------------------------------------

    async def list_keys(self) -> Any:
        return await self._get("/v2/ListKeys")

    async def get_key_info(
        self,
        *,
        id: str | None = None,
        search: str | None = None,
        show_secret_key: bool = False,
    ) -> Any:
        return await self._get(
            "/v2/GetKeyInfo",
            {"id": id, "search": search, "showSecretKey": show_secret_key},
        )
