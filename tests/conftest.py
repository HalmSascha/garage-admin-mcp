from __future__ import annotations

import pytest

from garage_admin_mcp.client import GarageAdminClient


@pytest.fixture
async def client() -> GarageAdminClient:
    c = GarageAdminClient(base_url="http://garage.test:3903", token="test-token")
    yield c
    await c.aclose()
