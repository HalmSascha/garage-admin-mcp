"""Read-only cluster-level tools (status, health, statistics, layout, nodes)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_cluster_status() -> Any:
        """Get the current status of the Garage cluster: member nodes, their
        roles/zones/capacities, and whether each node is currently connected.
        Use this to get a quick overview of the whole cluster."""
        return await get_client().get_cluster_status()

    @mcp.tool
    async def get_cluster_health() -> Any:
        """Get the health of the Garage cluster (connected/known nodes,
        storage node quorum, partition status). Use this to check whether
        the cluster is able to serve reads/writes right now."""
        return await get_client().get_cluster_health()

    @mcp.tool
    async def get_cluster_statistics() -> Any:
        """Get freeform, human-readable cluster statistics (the same text
        the `garage stats` CLI command prints), including per-node storage
        usage and object counts."""
        return await get_client().get_cluster_statistics()

    @mcp.tool
    async def get_cluster_layout() -> Any:
        """Get the current cluster layout: how storage capacity is assigned
        to each node/zone, and any staged (not-yet-applied) layout changes."""
        return await get_client().get_cluster_layout()

    @mcp.tool
    async def get_node_info(node: str) -> Any:
        """Get detailed information about a single cluster node (identified
        by its node ID, as seen in get_cluster_status), such as its Garage
        version and configuration.

        Args:
            node: Node ID (or `self` for the node the admin API is served from).
        """
        return await get_client().get_node_info(node)

    @mcp.tool
    async def get_node_statistics(node: str) -> Any:
        """Get statistics for a single cluster node (identified by its node
        ID, as seen in get_cluster_status), such as storage usage and block
        counts.

        Args:
            node: Node ID (or `self` for the node the admin API is served from).
        """
        return await get_client().get_node_statistics(node)
