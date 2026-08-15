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
        return await self._request("GET", path, params=params)

    async def _post(
        self,
        path: str,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("POST", path, json_body=json_body, params=params)

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        response = await self._client.request(method, path, params=params, json=json_body)
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

    # -- Buckets (write) -----------------------------------------------------

    async def create_bucket(self, *, global_alias: str | None = None) -> Any:
        body: dict[str, Any] = {}
        if global_alias is not None:
            body["globalAlias"] = global_alias
        return await self._post("/v2/CreateBucket", json_body=body)

    async def update_bucket(
        self,
        id: str,
        *,
        quotas_max_size: int | None = None,
        quotas_max_objects: int | None = None,
        website_enabled: bool | None = None,
        website_index_document: str | None = None,
        website_error_document: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {}
        if quotas_max_size is not None or quotas_max_objects is not None:
            # Garage requires both quota fields together; an absent one
            # means "no limit" (null), it cannot be left unspecified.
            body["quotas"] = {"maxSize": quotas_max_size, "maxObjects": quotas_max_objects}
        if website_enabled is not None:
            website: dict[str, Any] = {"enabled": website_enabled}
            if website_index_document is not None:
                website["indexDocument"] = website_index_document
            if website_error_document is not None:
                website["errorDocument"] = website_error_document
            body["websiteAccess"] = website
        return await self._post("/v2/UpdateBucket", json_body=body, params={"id": id})

    async def delete_bucket(self, id: str) -> Any:
        return await self._post("/v2/DeleteBucket", params={"id": id})

    async def add_bucket_alias(self, bucket_id: str, global_alias: str) -> Any:
        return await self._post(
            "/v2/AddBucketAlias", json_body={"bucketId": bucket_id, "globalAlias": global_alias}
        )

    async def remove_bucket_alias(self, bucket_id: str, global_alias: str) -> Any:
        return await self._post(
            "/v2/RemoveBucketAlias", json_body={"bucketId": bucket_id, "globalAlias": global_alias}
        )

    # -- Keys (write) --------------------------------------------------------

    async def create_key(self, *, name: str | None = None) -> Any:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        return await self._post("/v2/CreateKey", json_body=body)

    async def update_key(
        self, id: str, *, name: str | None = None, never_expires: bool | None = None
    ) -> Any:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if never_expires is not None:
            body["neverExpires"] = never_expires
        return await self._post("/v2/UpdateKey", json_body=body, params={"id": id})

    async def delete_key(self, id: str) -> Any:
        return await self._post("/v2/DeleteKey", params={"id": id})

    async def import_key(
        self, access_key_id: str, secret_access_key: str, *, name: str | None = None
    ) -> Any:
        body: dict[str, Any] = {"accessKeyId": access_key_id, "secretAccessKey": secret_access_key}
        if name is not None:
            body["name"] = name
        return await self._post("/v2/ImportKey", json_body=body)

    # -- Permissions -----------------------------------------------------

    async def allow_bucket_key(
        self,
        bucket_id: str,
        access_key_id: str,
        *,
        read: bool = False,
        write: bool = False,
        owner: bool = False,
    ) -> Any:
        return await self._post(
            "/v2/AllowBucketKey",
            json_body={
                "bucketId": bucket_id,
                "accessKeyId": access_key_id,
                "permissions": {"read": read, "write": write, "owner": owner},
            },
        )

    async def deny_bucket_key(
        self,
        bucket_id: str,
        access_key_id: str,
        *,
        read: bool = False,
        write: bool = False,
        owner: bool = False,
    ) -> Any:
        return await self._post(
            "/v2/DenyBucketKey",
            json_body={
                "bucketId": bucket_id,
                "accessKeyId": access_key_id,
                "permissions": {"read": read, "write": write, "owner": owner},
            },
        )
