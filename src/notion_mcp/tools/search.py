"""
Search tools for Notion MCP server.
"""

import json
from typing import Any, Dict

import mcp
from mcp import types

# client is passed in from server.py


async def list_tools() -> list[types.Tool]:
    """List available search tools."""
    return [
        types.Tool(
            name="search",
            description="Search pages and data sources by title and other criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string to match against pages and data sources"
                    },
                    "filter": {
                        "type": "object",
                        "description": "Optional filter criteria",
                        "properties": {
                            "value": {"type": "string"},
                            "property": {"type": "string"}
                        }
                    },
                    "sort": {
                        "type": "object",
                        "description": "Optional sort criteria",
                        "properties": {
                            "direction": {"type": "string", "enum": ["ascending", "descending"]},
                            "timestamp": {"type": "string", "enum": ["created_time", "last_edited_time"]}
                        }
                    },
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
                    }
                },
                "required": ["query"]
            }
        )
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle search tool calls."""
    if name != "search":
        from mcp import types
        raise types.ToolError(f"Unknown search tool: {name}")
    
    client = await get_notion_client()
    
    try:
        query = arguments["query"]
        page_size = arguments.get("page_size", 20)
        start_cursor = arguments.get("start_cursor")
        
        # Build search parameters
        search_params = {
            "query": query,
            "page_size": min(page_size, 100)  # Enforce max 100
        }
        
        if start_cursor:
            search_params["start_cursor"] = start_cursor
        
        # Handle optional filter
        if "filter" in arguments:
            filter_params = arguments["filter"]
            if "value" in filter_params and "property" in filter_params:
                search_params["filter"] = {
                    "property": filter_params["property"],
                    "value": filter_params["value"]
                }
        
        # Handle optional sort
        if "sort" in arguments:
            sort_params = arguments["sort"]
            search_params["sort"] = {
                "direction": sort_params.get("direction", "ascending"),
                "timestamp": sort_params.get("timestamp", "last_edited_time")
            }
        
        # Execute search
        results = await client.search(**search_params)
        
        # Convert results to JSON string
        results_json = json.dumps(results, indent=2, ensure_ascii=False)
        
        return [types.TextContent(type="text", text=results_json)]
        
    except Exception as e:
        from mcp import types
        raise types.ToolError(f"Search failed: {str(e)}")