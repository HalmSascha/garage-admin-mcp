"""Write tools for buckets.

Only registered when GARAGE_ADMIN_READ_ONLY=false (see server.py). Kept in a
separate module from tools/buckets.py (which is always registered) so the
read/write boundary is visible at the file level, not just via a runtime flag.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def create_bucket(global_alias: str | None = None) -> Any:
        """Create a new bucket in Garage.

        Args:
            global_alias: Optional global name to give the bucket immediately
                (e.g. "my-app-backups"). If omitted, the bucket is created
                without an alias; use add_bucket_alias to name it later.
        """
        return await get_client().create_bucket(global_alias=global_alias)

    @mcp.tool
    async def update_bucket(
        id: str,
        quotas_max_size: int | None = None,
        quotas_max_objects: int | None = None,
        website_enabled: bool | None = None,
        website_index_document: str | None = None,
        website_error_document: str | None = None,
    ) -> Any:
        """Update a bucket's storage quotas and/or static-website
        configuration. Only the arguments you pass are changed; the rest of
        the bucket's configuration is left as-is.

        Quota note (Garage requirement, not a limitation of this tool): the
        two quota fields cannot be changed independently. If you set only
        quotas_max_size, quotas_max_objects is reset to "no limit" (and vice
        versa) - pass both together if you want to keep an existing limit.

        Website note: website_index_document is required when enabling the
        website (website_enabled=True); when disabling it
        (website_enabled=False), neither index nor error document should be
        set.

        Out of scope for this tool (use the garage CLI or web UI instead):
        CORS rules, lifecycle rules.

        Args:
            id: The bucket's Garage-internal ID (as returned by list_buckets).
            quotas_max_size: Maximum total size in bytes, or None for no limit.
            quotas_max_objects: Maximum object count, or None for no limit.
            website_enabled: Enable/disable serving this bucket as a static website.
            website_index_document: Index document filename (e.g. "index.html").
            website_error_document: Error document filename (optional).
        """
        return await get_client().update_bucket(
            id,
            quotas_max_size=quotas_max_size,
            quotas_max_objects=quotas_max_objects,
            website_enabled=website_enabled,
            website_index_document=website_index_document,
            website_error_document=website_error_document,
        )

    @mcp.tool
    async def delete_bucket(id: str, confirm_id: str) -> Any:
        """Permanently delete a bucket. THIS CANNOT BE UNDONE. Garage
        refuses the request if the bucket still contains objects.

        To prevent an LLM from deleting the wrong bucket based on an
        ambiguous instruction, confirm_id is required and must be
        byte-for-byte identical to id - the call is rejected locally,
        before any request reaches Garage, if they don't match.

        Args:
            id: The bucket's Garage-internal ID (as returned by list_buckets).
            confirm_id: Must equal id exactly.
        """
        if confirm_id != id:
            raise ValueError(
                f"confirm_id ({confirm_id!r}) does not match id ({id!r}) - "
                "refusing to delete. Pass the exact bucket id in both "
                "arguments to confirm."
            )
        return await get_client().delete_bucket(id)

    @mcp.tool
    async def add_bucket_alias(bucket_id: str, global_alias: str) -> Any:
        """Give a bucket an additional global alias/name. A bucket can have
        several aliases at once.

        Args:
            bucket_id: The bucket's Garage-internal ID.
            global_alias: The new global alias to add.
        """
        return await get_client().add_bucket_alias(bucket_id, global_alias)

    @mcp.tool
    async def remove_bucket_alias(bucket_id: str, global_alias: str) -> Any:
        """Remove a global alias from a bucket. Garage refuses if this
        would leave the bucket with no aliases and no local aliases either
        (a bucket must remain reachable by at least one name).

        Args:
            bucket_id: The bucket's Garage-internal ID.
            global_alias: The global alias to remove.
        """
        return await get_client().remove_bucket_alias(bucket_id, global_alias)
