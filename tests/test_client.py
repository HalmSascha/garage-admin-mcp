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


@pytest.mark.asyncio
@respx.mock
async def test_create_bucket_sends_global_alias(client: GarageAdminClient) -> None:
    route = respx.post("http://garage.test:3903/v2/CreateBucket").mock(
        return_value=httpx.Response(200, json={"id": "newbucket"})
    )

    await client.create_bucket(global_alias="my-bucket")

    import json

    assert json.loads(route.calls.last.request.content) == {"globalAlias": "my-bucket"}


@pytest.mark.asyncio
@respx.mock
async def test_update_bucket_sends_both_quota_fields_together(client: GarageAdminClient) -> None:
    route = respx.post("http://garage.test:3903/v2/UpdateBucket").mock(return_value=httpx.Response(200, json={}))

    await client.update_bucket("bucket1", quotas_max_size=1000)

    import json

    body = json.loads(route.calls.last.request.content)
    assert body == {"quotas": {"maxSize": 1000, "maxObjects": None}}
    assert route.calls.last.request.url.params["id"] == "bucket1"


@pytest.mark.asyncio
@respx.mock
async def test_delete_bucket_passes_id_as_query_param(client: GarageAdminClient) -> None:
    route = respx.post("http://garage.test:3903/v2/DeleteBucket").mock(return_value=httpx.Response(204))

    await client.delete_bucket("bucket1")

    assert route.calls.last.request.url.params["id"] == "bucket1"


@pytest.mark.asyncio
@respx.mock
async def test_allow_bucket_key_sends_permissions_object(client: GarageAdminClient) -> None:
    route = respx.post("http://garage.test:3903/v2/AllowBucketKey").mock(
        return_value=httpx.Response(200, json={})
    )

    await client.allow_bucket_key("bucket1", "key1", read=True)

    import json

    assert json.loads(route.calls.last.request.content) == {
        "bucketId": "bucket1",
        "accessKeyId": "key1",
        "permissions": {"read": True, "write": False, "owner": False},
    }


@pytest.mark.asyncio
@respx.mock
async def test_import_key_sends_secret_in_body(client: GarageAdminClient) -> None:
    route = respx.post("http://garage.test:3903/v2/ImportKey").mock(return_value=httpx.Response(200, json={}))

    await client.import_key("AKIA...", "supersecret", name="imported")

    import json

    assert json.loads(route.calls.last.request.content) == {
        "accessKeyId": "AKIA...",
        "secretAccessKey": "supersecret",
        "name": "imported",
    }
