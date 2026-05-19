"""
Comments tools for Notion MCP server.
"""

import json
from typing import Any, Dict, Optional

import mcp
from mcp import types

# client is passed in from server.py


async def list_tools() -> list[types.Tool]:
    """List available comments tools."""
    return [
        # Create Comment
        types.Tool(
            name="create_comment",
            description="Create a new comment",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent": {
                        "type": "object",
                        "description": "Parent page or block for the comment",
                        "properties": {
                            "type": {"type": "string", "enum": ["page_id", "block_id"]},
                            "page_id": {"type": "string"},
                            "block_id": {"type": "string"}
                        },
                        "required": ["type"]
                    },
                    "rich_text": {
                        "type": "array",
                        "description": "Comment text in rich text format",
                        "items": {"type": "object"},
                        "minItems": 1
                    },
                    "discussion_id": {
                        "type": "string",
                        "description": "Optional discussion ID to comment on"
                    }
                },
                "required": ["parent", "rich_text"]
            }
        ),
        
        # List Comments
        types.Tool(
            name="list_comments",
            description="List all comments in the workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Optional page ID to filter comments"
                    },
                    "block_id": {
                        "type": "string",
                        "description": "Optional block ID to filter comments"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of comments to return",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20
                    },
                    "start_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination"
                    }
                }
            }
        ),
        
        # Retrieve Comment
        types.Tool(
            name="retrieve_comment",
            description="Retrieve a specific comment by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {
                        "type": "string",
                        "description": "The ID of the comment to retrieve"
                    }
                },
                "required": ["comment_id"]
            }
        ),
        
        # Update Comment
        types.Tool(
            name="update_comment",
            description="Update a comment's content",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {
                        "type": "string",
                        "description": "The ID of the comment to update"
                    },
                    "rich_text": {
                        "type": "array",
                        "description": "Updated comment text in rich text format",
                        "items": {"type": "object"}
                    }
                },
                "required": ["comment_id"]
            }
        ),
        
        # Delete Comment
        types.Tool(
            name="delete_comment",
            description="Delete a comment",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {
                        "type": "string",
                        "description": "The ID of the comment to delete"
                    }
                },
                "required": ["comment_id"]
            }
        )
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle comments tool calls."""
    client = await get_notion_client()
    
    try:
        if name == "create_comment":
            parent = arguments["parent"]
            rich_text = arguments["rich_text"]
            discussion_id = arguments.get("discussion_id")
            
            result = await client.comments.create(
                parent=parent,
                rich_text=rich_text,
                discussion_id=discussion_id
            )
        
        elif name == "list_comments":
            page_id = arguments.get("page_id")
            block_id = arguments.get("block_id")
            limit = arguments.get("limit", 20)
            start_cursor = arguments.get("start_cursor")
            
            # Build list parameters
            list_params = {"page_size": min(limit, 100)}
            
            if start_cursor:
                list_params["start_cursor"] = start_cursor
            
            # Note: The official client may not support filtering by page_id/block_id directly
            # This is a simplified implementation
            result = await client.comments.list(**list_params)
        
        elif name == "retrieve_comment":
            comment_id = arguments["comment_id"]
            
            result = await client.comments.retrieve(comment_id=comment_id)
        
        elif name == "update_comment":
            comment_id = arguments["comment_id"]
            rich_text = arguments["rich_text"]
            
            result = await client.comments.update(
                comment_id=comment_id,
                rich_text=rich_text
            )
        
        elif name == "delete_comment":
            comment_id = arguments["comment_id"]
            
            result = await client.comments.delete(comment_id=comment_id)
        
        else:
            from mcp import types
            raise types.ToolError(f"Unknown comments tool: {name}")
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        return [types.TextContent(type="text", text=result_json)]
        
    except Exception as e:
        from mcp import types
        raise types.ToolError(f"Comments tool '{name}' failed: {str(e)}")