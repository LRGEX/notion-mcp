"""
Blocks tools for Notion MCP server.
"""

import json
from typing import Any, Dict, List, Optional

import mcp
from mcp import types

# client is passed in from server.py


async def list_tools() -> list[types.Tool]:
    """List available blocks tools."""
    return [
        # Retrieve Block
        types.Tool(
            name="retrieve_block",
            description="Retrieve a block by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_id": {
                        "type": "string",
                        "description": "The ID of the block to retrieve"
                    },
                    "filter_properties": {
                        "type": "array",
                        "description": "Optional list of properties to retrieve",
                        "items": {"type": "string"}
                    }
                },
                "required": ["block_id"]
            }
        ),
        
        # Retrieve Block Children
        types.Tool(
            name="retrieve_block_children",
            description="List child blocks of a parent block",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_id": {
                        "type": "string",
                        "description": "The ID of the parent block"
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
                    },
                    "filter": {
                        "type": "object",
                        "description": "Optional filter criteria"
                    }
                },
                "required": ["block_id"]
            }
        ),
        
        # Append Block Children
        types.Tool(
            name="append_block_children",
            description="Append child blocks to a parent block",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_id": {
                        "type": "string",
                        "description": "The ID of the parent block"
                    },
                    "children": {
                        "type": "array",
                        "description": "Array of child blocks to append",
                        "items": {"type": "object"},
                        "minItems": 1
                    }
                },
                "required": ["block_id", "children"]
            }
        ),
        
        # Update Block
        types.Tool(
            name="update_block",
            description="Update a block's properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_id": {
                        "type": "string",
                        "description": "The ID of the block to update"
                    },
                    "properties": {
                        "type": "object",
                        "description": "New properties for the block"
                    },
                    " archived": {
                        "type": "boolean",
                        "description": "Whether to archive the block"
                    }
                },
                "required": ["block_id"]
            }
        ),
        
        # Delete Block
        types.Tool(
            name="delete_block",
            description="Delete a block",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_id": {
                        "type": "string",
                        "description": "The ID of the block to delete"
                    }
                },
                "required": ["block_id"]
            }
        )
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle blocks tool calls."""
    client = await get_notion_client()
    
    try:
        if name == "retrieve_block":
            block_id = arguments["block_id"]
            filter_properties = arguments.get("filter_properties")
            
            result = await client.blocks.retrieve(
                block_id=block_id,
                filter_properties=filter_properties
            )
        
        elif name == "retrieve_block_children":
            block_id = arguments["block_id"]
            page_size = arguments.get("page_size", 20)
            start_cursor = arguments.get("start_cursor")
            filter_criteria = arguments.get("filter")
            
            # Build retrieve parameters
            retrieve_params = {
                "page_size": min(page_size, 100)
            }
            
            if start_cursor:
                retrieve_params["start_cursor"] = start_cursor
            if filter_criteria:
                retrieve_params["filter"] = filter_criteria
            
            result = await client.blocks.children.retrieve(
                block_id=block_id,
                **retrieve_params
            )
        
        elif name == "append_block_children":
            block_id = arguments["block_id"]
            children = arguments["children"]
            
            result = await client.blocks.children.append(
                block_id=block_id,
                children=children
            )
        
        elif name == "update_block":
            block_id = arguments["block_id"]
            properties = arguments.get("properties")
            archived = arguments.get("archived")
            
            update_params = {}
            if properties:
                update_params["properties"] = properties
            if archived is not None:
                update_params["archived"] = archived
            
            result = await client.blocks.update(
                block_id=block_id,
                **update_params
            )
        
        elif name == "delete_block":
            block_id = arguments["block_id"]
            
            # Note: Delete blocks by setting archived=True
            result = await client.blocks.update(
                block_id=block_id,
                archived=True
            )
        
        else:
            from mcp import types
            raise types.ToolError(f"Unknown blocks tool: {name}")
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        return [types.TextContent(type="text", text=result_json)]
        
    except Exception as e:
        from mcp import types
        raise types.ToolError(f"Blocks tool '{name}' failed: {str(e)}")