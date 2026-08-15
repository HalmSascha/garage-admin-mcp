"""Tests that the FastMCP app registers exactly the expected V1 (read-only)
tool set, and that get_key_info's signature has no way to request secrets."""

from __future__ import annotations

import inspect

import pytest

from garage_admin_mcp.server import create_app
from garage_admin_mcp.settings import Settings

EXPECTED_V1_TOOLS = {
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


@pytest.fixture
def settings() -> Settings:
    return Settings(url="http://garage.test:3903", token="test-token")


@pytest.mark.asyncio
async def test_registers_exactly_the_expected_v1_tools(settings: Settings) -> None:
    app = create_app(settings)

    tools = await app.list_tools()

    assert {t.name for t in tools} == EXPECTED_V1_TOOLS


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
