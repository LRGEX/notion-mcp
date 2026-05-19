# Notion MCP Server

**Version 0.1.0**

Stateless MCP server exposing the full Notion API as 33 tools over streamable-http transport. No server-side secrets — each user passes their own Notion integration token via `Authorization` header.

## Prerequisites

- **Notion Integration Token** — required for every user who connects
- **Docker** (for deployment) or **Python 3.13+** with **uv** (for local development)

## Notion Integration Setup

Every user needs their own Notion integration token. Create one per user:

1. Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations)
2. Click **"New integration"**
3. Give it a name (e.g., "MCP - John")
4. Select the workspace
5. Click **Submit** — you'll get a token starting with `ntn_`
6. **Share pages with the integration**: open each page/database in Notion, click the `...` menu → **Connections** → **Add connection** → select your integration name

The integration only has access to pages explicitly shared with it. Without sharing, `search_pages` returns nothing.

## Deploy with Docker

```bash
git clone https://github.com/LRGEX/notion-mcp.git
cd notion-mcp
docker compose build
docker compose up -d
```

Server starts on **port 9201**. Verify it's running:

```bash
curl -X POST http://localhost:9201/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}'
```

Expected response: JSON with `"result"` containing server capabilities.

## Connect an MCP Client

### Oh My Pi

Add to `~/.omp/agent/mcp.json` or `.omp/mcp.json`:

```json
{
  "$schema": "https://raw.githubusercontent.com/can1357/oh-my-pi/main/packages/coding-agent/src/config/mcp-schema.json",
  "mcpServers": {
    "notion": {
      "type": "sse",
      "url": "http://YOUR_SERVER_IP:9201/sse",
      "headers": {
        "Authorization": "Bearer ntn_your_integration_token_here"
      }
    }
  }
}
```

Replace `YOUR_SERVER_IP` with the server address (e.g., `192.168.1.101`).
Replace `ntn_your_integration_token_here` with your actual `ntn_` token from the integration setup above.

### Claude Desktop / Other MCP Clients

For any MCP client that supports SSE or streamable-http, point it at:

- **SSE endpoint**: `http://YOUR_SERVER_IP:9201/sse`
- **Streamable HTTP endpoint**: `http://YOUR_SERVER_IP:9201/mcp`

Pass the token in the `Authorization: Bearer ntn_xxx` header.

## Multi-User

Multiple users can connect to the same server simultaneously. Each user provides their own `ntn_` token in the `Authorization` header. The server is fully stateless — no sessions, no stored tokens, no `.env` file.

10 users = 10 different tokens, same Docker container, same port.

## Run Locally (without Docker)

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/LRGEX/notion-mcp.git
cd notion-mcp
uv sync
uv run notion-mcp
```

Server starts on `http://0.0.0.0:9201`.

## Tools (33)

All tools automatically use the token from the request's `Authorization` header. No token parameter is needed in any tool call.

### Meta

| Tool | Description |
|------|-------------|
| `list_notion_tools` | List all available Notion tools and their descriptions |

### Search

| Tool | Description |
|------|-------------|
| `search_pages` | Search pages by title, with sort/filter/pagination |

### Pages

| Tool | Description |
|------|-------------|
| `create_page` | Create page with properties, content, icon, cover |
| `retrieve_page` | Get page by ID |
| `update_page` | Update page properties, content, icon, cover |
| `trash_page` | Move page to trash |
| `move_page` | Move page to new parent |
| `retrieve_page_as_markdown` | Get page content as markdown |
| `update_page_markdown` | Update page content via markdown string |

### Data Sources (Databases)

| Tool | Description |
|------|-------------|
| `create_data_source` | Create a data source |
| `retrieve_data_source` | Get data source by ID |
| `update_data_source` | Update data source properties |
| `query_data_source` | Query with filters/sorts/pagination |
| `list_data_source_templates` | List available templates |

### Databases

| Tool | Description |
|------|-------------|
| `retrieve_database` | Get database metadata and schema |

### Blocks

| Tool | Description |
|------|-------------|
| `retrieve_block` | Get block by ID |
| `retrieve_block_children` | List child blocks |
| `append_block_children` | Append blocks to parent |
| `update_block` | Update a block |
| `delete_block` | Delete a block |

### Comments

| Tool | Description |
|------|-------------|
| `create_comment` | Create a comment |
| `list_comments` | List comments with filters |
| `retrieve_comment` | Get comment by ID |
| `update_comment` | Update comment text |
| `delete_comment` | Delete a comment |

### Users

| Tool | Description |
|------|-------------|
| `list_users` | List workspace users |
| `retrieve_user` | Get user by ID |
| `retrieve_self` | Get authenticated user info |

### File Uploads

| Tool | Description |
|------|-------------|
| `create_file_upload` | Initiate file upload |
| `send_file_upload` | Send file data |
| `complete_file_upload` | Finalize upload |
| `list_file_uploads` | List file uploads |
| `retrieve_file_upload` | Get upload status |

## Architecture

- **Stateless** — no stored tokens, no sessions, no `.env` file
- **Auth via header** — reads `Authorization: Bearer ntn_xxx` from every request
- **Multi-user** — different tokens per connection, zero shared state
- **Transport** — streamable-http (primary) with SSE fallback
- **Framework** — FastMCP from the official `mcp` Python SDK
- **API client** — `notion-client` v3.1.0 (official Notion async client)

## Port Allocation

| Port | MCP Service |
|------|-------------|
| 9201 | Notion |
| 9202 | *(reserved)* |
| 9203 | *(reserved)* |

## Project Structure

```
notion_mcp/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── src/notion_mcp/
│   ├── __init__.py            # Package metadata
│   ├── client.py              # create_client(token) — stateless factory
│   ├── server.py              # FastMCP server — all 33 tool definitions
│   └── tools/                 # (unused — tools are inline in server.py)
│       ├── blocks.py
│       ├── comments.py
│       ├── data_sources.py
│       ├── databases.py
│       ├── files.py
│       ├── pages.py
│       ├── search.py
│       └── users.py
└── mcp_configs/
    └── notion.json            # MCP client config reference
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | >=1.6.0 | MCP framework (FastMCP, transports) |
| `notion-client` | >=3.1.0 | Official Notion API async client |
| `pydantic` | >=2.0.0 | Parameter validation |

## License

Proprietary — LRGEX. All rights reserved.
