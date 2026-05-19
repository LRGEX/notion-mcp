# Notion MCP Server

Stateless MCP server exposing the full Notion API over SSE. No server-side secrets — each user passes their own Notion token via `Authorization` header.

Deployed on `192.168.1.101:9201`.

## Connect (Oh My Pi)

Add to `~/.omp/agent/mcp.json` or `.omp/mcp.json`:

```json
{
  "$schema": "https://raw.githubusercontent.com/can1357/oh-my-pi/main/packages/coding-agent/src/config/mcp-schema.json",
  "mcpServers": {
    "notion": {
      "type": "sse",
      "url": "http://192.168.1.101:9201/sse",
      "headers": {
        "Authorization": "Bearer ntn_your_notion_token_here"
      }
    }
  }
}
```

Each user puts their own `ntn_` token in the `Authorization` header. 10 users = 10 different tokens, all hitting the same endpoint.

## Architecture

- **Stateless** — no stored tokens, no sessions, no `.env` secrets
- **Auth via header** — reads `Authorization: Bearer ntn_xxx` from every request
- **Multi-user** — different tokens per connection, zero shared state
- **One port per MCP** — Notion = `9201`, future MCPs get 9202, 9203, …
- **SSE transport** — connect from any MCP client over HTTP

## Run Locally

```bash
uv run python -m src.notion_mcp.server
```

## Docker

```bash
docker compose build
docker compose up -d
docker compose logs -f
docker compose down
```

## Tools (32)

All tools automatically use the token from the request's `Authorization` header — no token parameter needed.

| Tool | Description |
|------|-------------|
| **Search** | |
| `search_pages` | Search pages by title, with sort/filter/pagination |
| **Pages** | |
| `create_page` | Create page with properties, content, icon, cover |
| `retrieve_page` | Get page by ID |
| `update_page` | Update page properties, content, icon, cover |
| `trash_page` | Move page to trash |
| `move_page` | Move page to new parent |
| `retrieve_page_as_markdown` | Get page content as markdown |
| `update_page_markdown` | Update page content via markdown string |
| **Data Sources** | |
| `create_data_source` | Create a data source |
| `retrieve_data_source` | Get data source by ID |
| `update_data_source` | Update data source properties |
| `query_data_source` | Query with filters/sorts/pagination |
| `list_data_source_templates` | List available templates |
| **Databases** | |
| `retrieve_database` | Get database metadata and data source IDs |
| **Blocks** | |
| `retrieve_block` | Get block by ID |
| `retrieve_block_children` | List child blocks |
| `append_block_children` | Append blocks to parent |
| `update_block` | Update a block |
| `delete_block` | Delete a block |
| **Comments** | |
| `create_comment` | Create a comment |
| `list_comments` | List comments with filters |
| `retrieve_comment` | Get comment by ID |
| `update_comment` | Update comment text |
| `delete_comment` | Delete a comment |
| **Users** | |
| `list_users` | List workspace users |
| `retrieve_user` | Get user by ID |
| `retrieve_self` | Get authenticated user info |
| **File Uploads** | |
| `create_file_upload` | Initiate file upload |
| `send_file_upload` | Send file data |
| `complete_file_upload` | Finalize upload |
| `list_file_uploads` | List file uploads |
| `retrieve_file_upload` | Get upload status |

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
├── src/notion_mcp/
│   ├── client.py              # create_client(token) — stateless
│   ├── server.py              # FastMCP server, reads auth from headers
│   └── tools/
│       ├── search.py
│       ├── pages.py
│       ├── data_sources.py
│       ├── databases.py
│       ├── blocks.py
│       ├── comments.py
│       ├── users.py
│       └── files.py
└── mcp_configs/
    └── notion.json
```

## Dependencies

- `mcp>=1.6.0` — MCP framework (SSE transport)
- `notion-client>=3.1.0` — Official Notion API client
- `pydantic>=2.0.0` — Validation