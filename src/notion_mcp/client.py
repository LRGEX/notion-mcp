"""
Stateless Notion client — created per-request from Authorization header.
"""

import notion_client
from mcp.shared.exceptions import McpError, ErrorData


def create_client(token: str) -> notion_client.AsyncClient:
    """Create a Notion AsyncClient from a token. No state stored."""
    if not token:
        raise McpError(ErrorData(code=400, message="Authorization header required"))
    if not token.startswith("ntn_"):
        raise McpError(ErrorData(code=400, message="Invalid Notion token. Expected 'ntn_' prefix"))
    return notion_client.AsyncClient(options={"auth": token})