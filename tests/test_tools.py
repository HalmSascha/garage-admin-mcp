"""Tests that the FastMCP app registers exactly the expected V1 (read-only)
tool set, and that get_key_info's signature has no way to request secrets."""

from __future__ import annotations

import inspect

import pytest

from garage_admin_mcp.server import create_app
from garage_admin_mcp.settings import Settings

READ_ONLY_TOOLS = {
    "get_cluster_status",
    "get_cluster_health",
    "get_cluster_statistics",
    "get_cluster_layout",
    "get_node_info",
    "get_node_statistics",
    "list_buckets",
    "get_bucket_info",
    "list_keys",
    "get_key_info",
}

WRITE_TOOLS = {
    "create_bucket",
    "update_bucket",
    "delete_bucket",
    "add_bucket_alias",
    "remove_bucket_alias",
    "create_key",
    "update_key",
    "delete_key",
    "import_key",
    "allow_bucket_key",
    "deny_bucket_key",
}


@pytest.fixture
def settings() -> Settings:
    return Settings(url="http://garage.test:3903", token="test-token")


@pytest.mark.asyncio
async def test_read_only_default_registers_only_read_tools(settings: Settings) -> None:
    assert settings.read_only is True
    app = create_app(settings)

    tools = await app.list_tools()

    assert {t.name for t in tools} == READ_ONLY_TOOLS


@pytest.mark.asyncio
async def test_read_only_false_additionally_registers_write_tools() -> None:
    settings = Settings(url="http://garage.test:3903", token="test-token", read_only=False)
    app = create_app(settings)

    tools = await app.list_tools()

    assert {t.name for t in tools} == READ_ONLY_TOOLS | WRITE_TOOLS


def test_get_key_info_tool_has_no_secret_parameter() -> None:
    from garage_admin_mcp.tools.keys import register as register_keys

    captured = {}

    class FakeMCP:
        def tool(self, fn):
            captured[fn.__name__] = fn
            return fn

    register_keys(FakeMCP())

    signature = inspect.signature(captured["get_key_info"])
    assert "show_secret_key" not in signature.parameters
    assert "showSecretKey" not in signature.parameters


def _register_fake(register_fn):
    """Call a tools module's register(mcp) against a fake MCP that just
    captures the decorated functions, so we can call them directly without
    spinning up a full FastMCP app or a real GarageAdminClient."""
    captured = {}

    class FakeMCP:
        def tool(self, fn):
            captured[fn.__name__] = fn
            return fn

    register_fn(FakeMCP())
    return captured


@pytest.mark.asyncio
async def test_delete_bucket_rejects_mismatched_confirm_id_without_calling_garage() -> None:
    from garage_admin_mcp.tools.buckets_write import register as register_buckets_write

    tools = _register_fake(register_buckets_write)

    with pytest.raises(ValueError, match="does not match"):
        # No GarageAdminClient is set up in this test - if the mismatch
        # check didn't run first, this would fail with a different error
        # (RuntimeError from context.get_client()), which the assertion
        # below would also catch, so this test would fail either way if
        # the ordering regresses.
        await tools["delete_bucket"](id="abc", confirm_id="xyz")


@pytest.mark.asyncio
async def test_delete_key_rejects_mismatched_confirm_id_without_calling_garage() -> None:
    from garage_admin_mcp.tools.keys_write import register as register_keys_write

    tools = _register_fake(register_keys_write)

    with pytest.raises(ValueError, match="does not match"):
        await tools["delete_key"](id="abc", confirm_id="xyz")


@pytest.mark.asyncio
async def test_s3_tools_not_registered_without_s3_credentials() -> None:
    settings = Settings(url="http://garage.test:3903", token="test-token")
    assert settings.s3_url is None

    app = create_app(settings)
    tools = await app.list_tools()

    assert "list_s3_objects" not in {t.name for t in tools}
    assert "get_s3_object" not in {t.name for t in tools}


@pytest.mark.asyncio
async def test_s3_tools_registered_when_s3_credentials_configured() -> None:
    settings = Settings(
        url="http://garage.test:3903",
        token="test-token",
        s3_url="http://garage.test:3900",
        s3_access_key_id="AKIA...",
        s3_secret_access_key="secret",
    )

    app = create_app(settings)
    tools = await app.list_tools()

    assert {"list_s3_objects", "get_s3_object"} <= {t.name for t in tools}
