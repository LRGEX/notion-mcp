"""
Notion MCP server — stateless, reads token from Authorization header per request.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP, Context

from .client import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = FastMCP("notion-mcp", host="0.0.0.0", port=9201, json_response=True)


def _token(ctx: Context) -> str:
    """Extract Bearer token from request headers."""
    request = ctx.request_context.request
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    from mcp.shared.exceptions import McpError, ErrorData
    raise McpError(
        ErrorData(code=401, message="Missing or invalid Authorization header. Use: Bearer ntn_your_token")
    )


def _json(obj: Any) -> str:
    """Serialize to JSON string for MCP text response."""
    return json.dumps(obj, indent=2, ensure_ascii=False) if not isinstance(obj, str) else obj


# ── Meta ────────────────────────────────────────────────────────────

@server.tool()
async def list_notion_tools() -> List[Dict[str, Any]]:
    """List all available Notion tools."""
    tools = await server._tool_manager.list_tools()
    return [{"name": t.name, "description": t.description} for t in tools]


# ── Search ──────────────────────────────────────────────────────────

@server.tool()
async def search_pages(ctx: Context, query: str, sort: Optional[Dict[str, Any]] = None, filter: Optional[Dict[str, Any]] = None, start_cursor: Optional[str] = None, page_size: Optional[int] = None) -> str:
    """Search for Notion pages."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"query": query}
    if sort:
        params["sort"] = sort
    if filter:
        params["filter"] = filter
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = min(page_size, 100)
    result = await client.search(**params)
    
    return _json(result)


# ── Pages ───────────────────────────────────────────────────────────

@server.tool()
async def create_page(ctx: Context, parent: Dict[str, Any], properties: Dict[str, Any], content: Optional[List[Dict[str, Any]]] = None, icon: Optional[Dict[str, Any]] = None, cover: Optional[Dict[str, Any]] = None, is_template: Optional[bool] = None, archived: Optional[bool] = None) -> str:
    """Create a new Notion page."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"parent": parent, "properties": properties}
    if icon:
        params["icon"] = icon
    if cover:
        params["cover"] = cover
    if is_template is not None:
        params["is_template"] = is_template
    if archived is not None:
        params["archived"] = archived
    result = await client.pages.create(**params)
    if content:
        await client.blocks.children.append(block_id=result["id"], children=content)
    
    return _json(result)


@server.tool()
async def retrieve_page(ctx: Context, page_id: str) -> str:
    """Retrieve a Notion page by ID."""
    client = create_client(_token(ctx))
    result = await client.pages.retrieve(page_id=page_id)
    
    return _json(result)


@server.tool()
async def update_page(ctx: Context, page_id: str, properties: Optional[Dict[str, Any]] = None, content: Optional[List[Dict[str, Any]]] = None, icon: Optional[Dict[str, Any]] = None, cover: Optional[Dict[str, Any]] = None, archived: Optional[bool] = None) -> str:
    """Update a Notion page."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"page_id": page_id}
    if properties:
        params["properties"] = properties
    if icon:
        params["icon"] = icon
    if cover:
        params["cover"] = cover
    if archived is not None:
        params["archived"] = archived
    result = await client.pages.update(**params)
    if content:
        await client.blocks.children.append(block_id=page_id, children=content)
    
    return _json(result)


@server.tool()
async def trash_page(ctx: Context, page_id: str) -> str:
    """Move a page to trash."""
    client = create_client(_token(ctx))
    result = await client.pages.update(page_id=page_id, archived=True)
    
    return _json(result)


@server.tool()
async def move_page(ctx: Context, page_id: str, parent: Dict[str, Any], after: Optional[Dict[str, Any]] = None) -> str:
    """Move a page to a new location."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"page_id": page_id, "parent": parent}
    if after:
        params["after"] = after
    result = await client.pages.update(**params)
    
    return _json(result)


@server.tool()
async def retrieve_page_as_markdown(ctx: Context, page_id: str) -> str:
    """Retrieve a Notion page as markdown."""
    client = create_client(_token(ctx))
    page = await client.pages.retrieve(page_id=page_id)
    blocks = await client.blocks.children.list(block_id=page_id)

    def _block_to_md(block: Dict) -> str:
        btype = block.get("type", "")
        data = block.get(btype, {})
        texts = data.get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in texts)
        if btype == "heading_1":
            return f"# {text}"
        elif btype == "heading_2":
            return f"## {text}"
        elif btype == "heading_3":
            return f"### {text}"
        elif btype == "paragraph":
            return text
        elif btype == "bulleted_list_item":
            return f"- {text}"
        elif btype == "numbered_list_item":
            return f"1. {text}"
        elif btype == "to_do":
            checked = data.get("checked", False)
            return f"- [{'x' if checked else ' '}] {text}"
        elif btype == "code":
            lang = data.get("language", "")
            return f"```{lang}\n{text}\n```"
        elif btype == "quote":
            return f"> {text}"
        elif btype == "divider":
            return "---"
        elif btype == "image":
            src = data.get("file", {}).get("url", data.get("external", {}).get("url", ""))
            return f"![{text}]({src})" if src else text
        return text

    lines = [_block_to_md(b) for b in blocks.get("results", [])]
    title = ""
    props = page.get("properties", {})
    for v in props.values():
        if v.get("type") == "title":
            title_items = v.get("title", [])
            title = "".join(t.get("plain_text", "") for t in title_items)
            break

    md = f"# {title}\n\n" + "\n\n".join(lines) if title else "\n\n".join(lines)
    
    return md


@server.tool()
async def update_page_markdown(ctx: Context, page_id: str, content: str, properties: Optional[Dict[str, Any]] = None) -> str:
    """Update a Notion page with markdown content."""
    client = create_client(_token(ctx))
    # Split content into paragraphs as blocks
    lines = content.split("\n")
    children = []
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("### "):
            children.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}})
        elif line.startswith("## "):
            children.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}})
        elif line.startswith("# "):
            children.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("- "):
            children.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        else:
            children.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}})

    params: Dict[str, Any] = {"page_id": page_id}
    if properties:
        params["properties"] = properties
    result = await client.pages.update(**params)
    if children:
        await client.blocks.children.append(block_id=page_id, children=children)
    
    return _json(result)


# ── Data Sources ────────────────────────────────────────────────────

@server.tool()
async def create_data_source(ctx: Context, source: Dict[str, Any], parent: Optional[Dict[str, Any]] = None) -> str:
    """Create a data source."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"source": source}
    if parent:
        params["parent"] = parent
    result = await client.data_sources.create(**params)
    
    return _json(result)


@server.tool()
async def retrieve_data_source(ctx: Context, data_source_id: str) -> str:
    """Retrieve a data source by ID."""
    client = create_client(_token(ctx))
    result = await client.data_sources.retrieve(data_source_id=data_source_id)
    
    return _json(result)


@server.tool()
async def update_data_source(ctx: Context, data_source_id: str, source: Dict[str, Any]) -> str:
    """Update a data source."""
    client = create_client(_token(ctx))
    result = await client.data_sources.update(data_source_id=data_source_id, source=source)
    
    return _json(result)


@server.tool()
async def query_data_source(ctx: Context, data_source_id: str, filter_properties: Optional[List[str]] = None, filter: Optional[Dict[str, Any]] = None, sort: Optional[List[Dict[str, Any]]] = None, start_cursor: Optional[str] = None, page_size: Optional[int] = None) -> str:
    """Query a data source."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"data_source_id": data_source_id}
    if filter_properties:
        params["filter_properties"] = filter_properties
    if filter:
        params["filter"] = filter
    if sort:
        params["sort"] = sort
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = page_size
    result = await client.data_sources.query(**params)
    
    return _json(result)


@server.tool()
async def list_data_source_templates(ctx: Context) -> str:
    """List available data source templates."""
    client = create_client(_token(ctx))
    result = await client.data_sources.list_templates()
    
    return _json(result)


# ── Databases ───────────────────────────────────────────────────────

@server.tool()
async def retrieve_database(ctx: Context, database_id: str) -> str:
    """Retrieve a Notion database by ID."""
    client = create_client(_token(ctx))
    result = await client.databases.retrieve(database_id=database_id)
    
    return _json(result)


# ── Blocks ──────────────────────────────────────────────────────────

@server.tool()
async def retrieve_block(ctx: Context, block_id: str) -> str:
    """Retrieve a Notion block by ID."""
    client = create_client(_token(ctx))
    result = await client.blocks.retrieve(block_id=block_id)
    
    return _json(result)


@server.tool()
async def retrieve_block_children(ctx: Context, block_id: str, start_cursor: Optional[str] = None, page_size: Optional[int] = None) -> str:
    """Retrieve children of a Notion block."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"block_id": block_id}
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = page_size
    result = await client.blocks.children.list(**params)
    
    return _json(result)


@server.tool()
async def append_block_children(ctx: Context, block_id: str, children: List[Dict[str, Any]]) -> str:
    """Append children to a Notion block."""
    client = create_client(_token(ctx))
    result = await client.blocks.children.append(block_id=block_id, children=children)
    
    return _json(result)


@server.tool()
async def update_block(ctx: Context, block_id: str, archived: Optional[bool] = None) -> str:
    """Update a Notion block."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"block_id": block_id}
    if archived is not None:
        params["archived"] = archived
    result = await client.blocks.update(**params)
    
    return _json(result)


@server.tool()
async def delete_block(ctx: Context, block_id: str) -> str:
    """Delete a Notion block."""
    client = create_client(_token(ctx))
    result = await client.blocks.delete(block_id=block_id)
    
    return _json(result)


# ── Comments ────────────────────────────────────────────────────────

@server.tool()
async def create_comment(ctx: Context, parent: Dict[str, Any], rich_text: List[Dict[str, Any]], discussion_id: Optional[str] = None) -> str:
    """Create a comment."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"parent": parent, "rich_text": rich_text}
    if discussion_id:
        params["discussion_id"] = discussion_id
    result = await client.comments.create(**params)
    
    return _json(result)


@server.tool()
async def list_comments(ctx: Context, page_id: Optional[str] = None, block_id: Optional[str] = None, limit: Optional[int] = None, before_timestamp: Optional[str] = None, after_timestamp: Optional[str] = None, sort_direction: Optional[str] = None) -> str:
    """List comments."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {}
    if page_id:
        params["block_id"] = page_id
    elif block_id:
        params["block_id"] = block_id
    if limit:
        params["page_size"] = limit
    if before_timestamp:
        params["before_timestamp"] = before_timestamp
    if after_timestamp:
        params["after_timestamp"] = after_timestamp
    if sort_direction:
        params["sort_direction"] = sort_direction
    result = await client.comments.list(**params)
    
    return _json(result)


@server.tool()
async def retrieve_comment(ctx: Context, comment_id: str) -> str:
    """Retrieve a comment by ID."""
    client = create_client(_token(ctx))
    result = await client.comments.retrieve(comment_id=comment_id)
    
    return _json(result)


@server.tool()
async def update_comment(ctx: Context, comment_id: str, rich_text: List[Dict[str, Any]]) -> str:
    """Update a comment."""
    client = create_client(_token(ctx))
    result = await client.comments.update(comment_id=comment_id, rich_text=rich_text)
    
    return _json(result)


@server.tool()
async def delete_comment(ctx: Context, comment_id: str) -> str:
    """Delete a comment."""
    client = create_client(_token(ctx))
    result = await client.comments.delete(comment_id=comment_id)
    
    return _json(result)


# ── Users ───────────────────────────────────────────────────────────

@server.tool()
async def list_users(ctx: Context, start_cursor: Optional[str] = None, page_size: Optional[int] = None) -> str:
    """List all users in the Notion workspace."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {}
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = page_size
    result = await client.users.list(**params)
    
    return _json(result)


@server.tool()
async def retrieve_user(ctx: Context, user_id: str) -> str:
    """Retrieve a user by ID."""
    client = create_client(_token(ctx))
    result = await client.users.retrieve(user_id=user_id)
    
    return _json(result)


@server.tool()
async def retrieve_self(ctx: Context) -> str:
    """Retrieve the current user."""
    client = create_client(_token(ctx))
    result = await client.users.me()
    
    return _json(result)


# ── File Uploads ────────────────────────────────────────────────────

@server.tool()
async def create_file_upload(ctx: Context, files: List[Dict[str, Any]], name: Optional[str] = None, content_type: Optional[str] = None, block_id: Optional[str] = None) -> str:
    """Create a file upload."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {"files": files}
    if name:
        params["name"] = name
    if content_type:
        params["content_type"] = content_type
    if block_id:
        params["block_id"] = block_id
    result = await client.file_uploads.create(**params)
    
    return _json(result)


@server.tool()
async def send_file_upload(ctx: Context, upload_id: str, content: str) -> str:
    """Send file upload content."""
    client = create_client(_token(ctx))
    result = await client.file_uploads.send(upload_id=upload_id, content=content)
    
    return _json(result)


@server.tool()
async def complete_file_upload(ctx: Context, upload_id: str) -> str:
    """Complete a file upload."""
    client = create_client(_token(ctx))
    result = await client.file_uploads.complete(upload_id=upload_id)
    
    return _json(result)


@server.tool()
async def list_file_uploads(ctx: Context, limit: Optional[int] = None, sort_direction: Optional[str] = None, after_timestamp: Optional[str] = None) -> str:
    """List file uploads."""
    client = create_client(_token(ctx))
    params: Dict[str, Any] = {}
    if limit:
        params["page_size"] = limit
    if sort_direction:
        params["sort_direction"] = sort_direction
    if after_timestamp:
        params["after_timestamp"] = after_timestamp
    result = await client.file_uploads.list(**params)
    
    return _json(result)


@server.tool()
async def retrieve_file_upload(ctx: Context, file_id: str) -> str:
    """Retrieve a file upload by ID."""
    client = create_client(_token(ctx))
    result = await client.file_uploads.retrieve(file_id=file_id)
    
    return _json(result)


# ── Entry point ─────────────────────────────────────────────────────

def main():
    logger.info("Starting Notion MCP server on port 9201...")
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
