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

**V1 — read-only.** All currently available tools only read data; nothing
in this server can create, modify or delete anything in your Garage
cluster yet. Write tools (bucket/key creation and deletion, permission
grants) are a planned V2, gated behind explicit review.

## Tools

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
| `GARAGE_ADMIN_TOKEN` | yes | — | Bearer token for the admin API. **Use a scoped admin-token** (`garage admin-token create --scope ListBuckets,GetBucketInfo,ListKeys,GetKeyInfo,GetClusterStatus,GetClusterHealth,GetClusterStatistics,GetClusterLayout,GetNodeInfo,GetNodeStatistics ...`) rather than the static master `admin_token` from `garage.toml` — Garage's own docs recommend against using master tokens. |
| `GARAGE_ADMIN_READ_ONLY` | no | `true` | Reserved for V2; currently has no effect since only read tools exist. |
| `GARAGE_ADMIN_HTTP_HOST` | no | `0.0.0.0` | Host to bind the MCP HTTP transport to. |
| `GARAGE_ADMIN_HTTP_PORT` | no | `8000` | Port to bind the MCP HTTP transport to. |
| `GARAGE_ADMIN_REQUEST_TIMEOUT_SECONDS` | no | `10.0` | Timeout for requests to the Garage admin API. |

A `.env` file in the working directory is also read (useful for local
development).

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
