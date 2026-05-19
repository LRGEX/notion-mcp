"""
Databases tools for Notion MCP server.
"""

import json
from typing import Any, Dict

import mcp
from mcp import types

# client is passed in from server.py


async def list_tools() -> list[types.Tool]:
    """List available databases tools."""
    return [
        # Retrieve Database
        types.Tool(
            name="retrieve_database",
            description="Retrieve database metadata and data source IDs",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_id": {
                        "type": "string",
                        "description": "The ID of the database to retrieve"
                    },
                    "filter_properties": {
                        "type": "array",
                        "description": "Optional list of properties to retrieve",
                        "items": {"type": "string"}
                    },
                    "legacy_filters": {
                        "type": "object",
                        "description": "Optional legacy filter configuration"
                    },
                    "legacy_type": {
                        "type": "string",
                        "description": "Optional legacy type configuration"
                    },
                    "legacy_include": {
                        "type": "boolean",
                        "description": "Whether to include legacy information"
                    }
                },
                "required": ["database_id"]
            }
        )
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle databases tool calls."""
    if name != "retrieve_database":
        from mcp import types
        raise types.ToolError(f"Unknown databases tool: {name}")
    
    client = await get_notion_client()
    
    try:
        database_id = arguments["database_id"]
        filter_properties = arguments.get("filter_properties")
        legacy_filters = arguments.get("legacy_filters")
        legacy_type = arguments.get("legacy_type")
        legacy_include = arguments.get("legacy_include", False)
        
        # Build retrieve parameters
        retrieve_params = {}
        if filter_properties:
            retrieve_params["filter_properties"] = filter_properties
        if legacy_filters:
            retrieve_params["legacy_filters"] = legacy_filters
        if legacy_type:
            retrieve_params["legacy_type"] = legacy_type
        if legacy_include:
            retrieve_params["legacy_include"] = legacy_include
        
        # Retrieve database
        result = await client.databases.retrieve(
            database_id=database_id,
            **retrieve_params
        )
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        return [types.TextContent(type="text", text=result_json)]
        
    except Exception as e:
        from mcp import types
        raise types.ToolError(f"Database retrieve failed: {str(e)}")