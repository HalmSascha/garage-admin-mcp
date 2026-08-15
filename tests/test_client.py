from __future__ import annotations

import httpx
import pytest
import respx

from garage_admin_mcp.client import GarageAdminClient, GarageAdminError


@pytest.mark.asyncio
@respx.mock
async def test_list_buckets_sends_bearer_token_and_parses_json(client: GarageAdminClient) -> None:
    route = respx.get("http://garage.test:3903/v2/ListBuckets").mock(
        return_value=httpx.Response(200, json=[{"id": "abc", "globalAliases": ["plane"]}])
    )

    result = await client.list_buckets()

    assert route.called
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer test-token"
    assert result == [{"id": "abc", "globalAliases": ["plane"]}]


@pytest.mark.asyncio
@respx.mock
async def test_get_bucket_info_passes_query_params(client: GarageAdminClient) -> None:
    route = respx.get("http://garage.test:3903/v2/GetBucketInfo").mock(
        return_value=httpx.Response(200, json={"id": "abc"})
    )

    await client.get_bucket_info(global_alias="plane")

    request = route.calls.last.request
    assert request.url.params["globalAlias"] == "plane"
    assert "id" not in request.url.params
    assert "search" not in request.url.params


@pytest.mark.asyncio
@respx.mock
async def test_get_key_info_never_requests_secret_by_default(client: GarageAdminClient) -> None:
    route = respx.get("http://garage.test:3903/v2/GetKeyInfo").mock(
        return_value=httpx.Response(200, json={"id": "key1"})
    )

    await client.get_key_info(id="key1")

    request = route.calls.last.request
    assert request.url.params["showSecretKey"] == "false"


@pytest.mark.asyncio
@respx.mock
async def test_error_response_raises_garage_admin_error(client: GarageAdminClient) -> None:
    respx.get("http://garage.test:3903/v2/ListBuckets").mock(
        return_value=httpx.Response(403, json={"error": "Forbidden", "code": "Forbidden"})
    )

    with pytest.raises(GarageAdminError) as exc_info:
        await client.list_buckets()

    assert exc_info.value.status_code == 403
    assert exc_info.value.body == {"error": "Forbidden", "code": "Forbidden"}
