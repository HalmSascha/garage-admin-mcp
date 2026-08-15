# garage-admin-mcp

An [MCP](https://modelcontextprotocol.io/) server for the [Garage](https://garagehq.deuxfleurs.fr/) S3-compatible
object storage **Admin API** — bucket management, access-key management and
permission assignment, exposed as MCP tools for LLM agents.

Garage itself is S3-compatible, so plain object access (get/put/list
objects) is already well covered by generic S3 MCP servers such as
[txn2/mcp-s3](https://github.com/txn2/mcp-s3). This project instead covers
Garage's *administration* API (cluster status, buckets, keys, permissions —
served on a separate port, `3903` by default), which generic S3 tools don't
and can't reach.

## Status

**Read tools are always on. Write tools are opt-in** via
`GARAGE_ADMIN_READ_ONLY=false` (default: `true`, i.e. read-only). This flag
only controls which tools the *server offers* — the `GARAGE_ADMIN_TOKEN`
you configure must independently carry the matching Garage admin-token
scopes, so a misconfigured flag can't grant access the token itself
doesn't have. See [Configuration](#configuration).

## Tools

### Read-only (always registered)

| Tool | Garage Admin API operation | Description |
| --- | --- | --- |
| `get_cluster_status` | `GetClusterStatus` | Cluster nodes, roles, zones, capacities |
| `get_cluster_health` | `GetClusterHealth` | Quorum / partition health |
| `get_cluster_statistics` | `GetClusterStatistics` | Freeform stats (storage usage, object counts) |
| `get_cluster_layout` | `GetClusterLayout` | Current + staged storage layout |
| `get_node_info` | `GetNodeInfo` | Info for a single node |
| `get_node_statistics` | `GetNodeStatistics` | Statistics for a single node |
| `list_buckets` | `ListBuckets` | All buckets, IDs and aliases |
| `get_bucket_info` | `GetBucketInfo` | Full detail on one bucket |
| `list_keys` | `ListKeys` | All S3 access keys (no secrets) |
| `get_key_info` | `GetKeyInfo` | Full detail on one key, **secret access key never returned** (see below) |

### Write (only registered when `GARAGE_ADMIN_READ_ONLY=false`)

| Tool | Garage Admin API operation | Description |
| --- | --- | --- |
| `create_bucket` | `CreateBucket` | Create a bucket, optionally with a global alias |
| `update_bucket` | `UpdateBucket` | Change quotas and/or static-website config |
| `delete_bucket` | `DeleteBucket` | Delete an empty bucket — **requires `confirm_id`, see below** |
| `add_bucket_alias` | `AddBucketAlias` | Add a global alias to a bucket |
| `remove_bucket_alias` | `RemoveBucketAlias` | Remove a global alias from a bucket |
| `create_key` | `CreateKey` | Create a new S3 access key |
| `update_key` | `UpdateKey` | Rename a key / clear its expiration |
| `delete_key` | `DeleteKey` | Delete a key — **requires `confirm_id`, see below** |
| `import_key` | `ImportKey` | Register an existing key pair with Garage |
| `allow_bucket_key` | `AllowBucketKey` | Grant read/write/owner permissions on a bucket to a key |
| `deny_bucket_key` | `DenyBucketKey` | Revoke read/write/owner permissions on a bucket from a key |

Out of scope even in V2 (use the `garage` CLI or web UI instead): CORS
rules, lifecycle rules, cluster layout changes, repair operations,
admin-token management, and everything not listed above.

### Safety: delete confirmation

`delete_bucket` and `delete_key` both require a `confirm_id` argument that
must be **byte-for-byte identical** to the `id` you're deleting. The check
runs locally, before any request reaches Garage — this exists specifically
so an LLM can't delete the wrong resource from an ambiguous
natural-language instruction; it has to restate the exact ID.

### Permission semantics: `allow_bucket_key` / `deny_bucket_key`

Garage's own admin API docs carry an explicit disclaimer that these two
endpoints have an "unconventional semantic", and this server intentionally
does not paper over it: each call only touches the permission flags you
set to `true`. Flags left `false` are **not** touched — they keep whatever
permission they already had. There is no "set exactly these permissions"
call; use `allow_bucket_key` to grant and `deny_bucket_key` to revoke.

### Security note: secret access keys are never exposed

Garage's `GetKeyInfo` endpoint supports a `showSecretKey` parameter that
returns a key's S3 secret access key in cleartext. This server deliberately
does **not** expose that parameter to `get_key_info` — an MCP tool callable
from natural-language conversation is not a safe place to surface raw
credentials. If you need a key's secret, use the `garage` CLI or the
Garage web UI directly.

## Configuration

All configuration is via environment variables (prefix `GARAGE_ADMIN_`):

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `GARAGE_ADMIN_URL` | yes | — | Base URL of the Garage admin API, e.g. `http://192.0.2.10:3903` |
| `GARAGE_ADMIN_TOKEN` | yes | — | Bearer token for the admin API. **Use a scoped admin-token** (`garage admin-token create --scope ...`) rather than the static master `admin_token` from `garage.toml` — Garage's own docs recommend against using master tokens. The scope must match the tools you intend to enable, see below. |
| `GARAGE_ADMIN_READ_ONLY` | no | `true` | Set to `false` to additionally register the write tools listed above. Requires a token with the matching write scopes (see below) — this flag alone grants no access. |
| `GARAGE_ADMIN_HTTP_HOST` | no | `0.0.0.0` | Host to bind the MCP HTTP transport to. |
| `GARAGE_ADMIN_HTTP_PORT` | no | `8000` | Port to bind the MCP HTTP transport to. |
| `GARAGE_ADMIN_REQUEST_TIMEOUT_SECONDS` | no | `10.0` | Timeout for requests to the Garage admin API. |

A `.env` file in the working directory is also read (useful for local
development).

**Example scoped tokens:**

```bash
# Read-only (default) - matches the tools always registered
garage admin-token create --scope \
  ListBuckets,GetBucketInfo,ListKeys,GetKeyInfo,GetClusterStatus,\
  GetClusterHealth,GetClusterStatistics,GetClusterLayout,GetNodeInfo,\
  GetNodeStatistics garage-admin-mcp-readonly

# Read + write - matches all tools with GARAGE_ADMIN_READ_ONLY=false
garage admin-token create --scope \
  ListBuckets,GetBucketInfo,ListKeys,GetKeyInfo,GetClusterStatus,\
  GetClusterHealth,GetClusterStatistics,GetClusterLayout,GetNodeInfo,\
  GetNodeStatistics,CreateBucket,UpdateBucket,DeleteBucket,AddBucketAlias,\
  RemoveBucketAlias,CreateKey,UpdateKey,DeleteKey,ImportKey,\
  AllowBucketKey,DenyBucketKey garage-admin-mcp-readwrite
```

## Running locally

```bash
uv sync
export GARAGE_ADMIN_URL=http://192.0.2.10:3903
export GARAGE_ADMIN_TOKEN=<your-scoped-admin-token>
uv run garage-admin-mcp
```

The server serves streamable-HTTP MCP at `http://<host>:<port>/mcp`, and a
plain-text liveness check at `/healthz`.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
```

## License

MIT — see [LICENSE](./LICENSE).
