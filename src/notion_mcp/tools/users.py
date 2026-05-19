"""
Users tools for Notion MCP server.
"""

import json
from typing import Any, Dict

import mcp
from mcp import types

# client is passed in from server.py


async def list_tools() -> list[types.Tool]:
    """List available users tools."""
    return [
        # List Users
        types.Tool(
            name="list_users",
            description="List all users in the workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results to return (max 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20
                    },
                    "start_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination"
                    },
                    "filter": {
                        "type": "object",
                        "description": "Optional filter criteria",
                        "properties": {
                            "role": {"type": "string"},
                            "type": {"type": "string"}
                        }
                    }
                }
            }
        ),
        
        # Retrieve User
        types.Tool(
            name="retrieve_user",
            description="Retrieve a specific user by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The ID of the user to retrieve"
                    }
                },
                "required": ["user_id"]
            }
        ),
        
        # Retrieve Self
        types.Tool(
            name="retrieve_self",
            description="Get information about the authenticated user (bot)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle users tool calls."""
    client = await get_notion_client()
    
    try:
        if name == "list_users":
            page_size = arguments.get("page_size", 20)
            start_cursor = arguments.get("start_cursor")
            filter_criteria = arguments.get("filter")
            
            # Build list parameters
            list_params = {"page_size": min(page_size, 100)}
            
            if start_cursor:
                list_params["start_cursor"] = start_cursor
            if filter_criteria:
                list_params["filter"] = filter_criteria
            
            result = await client.users.list(**list_params)
        
        elif name == "retrieve_user":
            user_id = arguments["user_id"]
            
            result = await client.users.retrieve(user_id=user_id)
        
        elif name == "retrieve_self":
            result = await client.users.me()
        
        else:
            from mcp import types
            raise types.ToolError(f"Unknown users tool: {name}")
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        return [types.TextContent(type="text", text=result_json)]
        
    except Exception as e:
        from mcp import types
        raise types.ToolError(f"Users tool '{name}' failed: {str(e)}")