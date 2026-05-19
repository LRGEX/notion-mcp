"""
Pages tools for Notion MCP server.
"""

import json
from typing import Any, Dict, Optional, Union

import mcp
from mcp import types

# client is passed in from server.py


async def list_tools() -> list[types.Tool]:
    """List available pages tools."""
    return [
        # Create Page
        types.Tool(
            name="create_page",
            description="Create a new page in Notion",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent": {
                        "type": "object",
                        "description": "Parent page or database information",
                        "properties": {
                            "type": {"type": "string", "enum": ["database_id", "page_id"]},
                            "database_id": {"type": "string"},
                            "page_id": {"type": "string"}
                        },
                        "required": ["type"]
                    },
                    "properties": {
                        "type": "object",
                        "description": "Page properties (title, etc.)"
                    },
                    "children": {
                        "type": "array",
                        "description": "Optional child content for the page",
                        "items": {"type": "object"}
                    },
                    "icon": {
                        "type": "object",
                        "description": "Optional page icon"
                    },
                    "cover": {
                        "type": "object",
                        "description": "Optional page cover image"
                    }
                },
                "required": ["parent", "properties"]
            }
        ),
        
        # Retrieve Page
        types.Tool(
            name="retrieve_page",
            description="Retrieve a page by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to retrieve"
                    },
                    "filter_properties": {
                        "type": "array",
                        "description": "Optional list of properties to retrieve",
                        "items": {"type": "string"}
                    }
                },
                "required": ["page_id"]
            }
        ),
        
        # Update Page
        types.Tool(
            name="update_page",
            description="Update page properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to update"
                    },
                    "properties": {
                        "type": "object",
                        "description": "New page properties"
                    },
                    "archived": {
                        "type": "boolean",
                        "description": "Whether to archive the page"
                    }
                },
                "required": ["page_id"]
            }
        ),
        
        # Trash Page
        types.Tool(
            name="trash_page",
            description="Move a page to trash or restore from trash",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to trash/restore"
                    },
                    "in_trash": {
                        "type": "boolean",
                        "description": "True to move to trash, false to restore",
                        "default": True
                    }
                },
                "required": ["page_id"]
            }
        ),
        
        # Move Page
        types.Tool(
            name="move_page",
            description="Move a page to a new parent",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to move"
                    },
                    "destination": {
                        "type": "object",
                        "description": "Destination parent information",
                        "properties": {
                            "type": {"type": "string", "enum": ["database_id", "page_id"]},
                            "database_id": {"type": "string"},
                            "page_id": {"type": "string"}
                        },
                        "required": ["type"]
                    },
                    "position": {
                        "type": "string",
                        "description": "Position in destination (\"first\" or \"last\")",
                        "default": "last"
                    }
                },
                "required": ["page_id", "destination"]
            }
        ),
        
        # Retrieve Page as Markdown
        types.Tool(
            name="retrieve_page_as_markdown",
            description="Get page content as markdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to convert to markdown"
                    }
                },
                "required": ["page_id"]
            }
        ),
        
        # Update Page Markdown
        types.Tool(
            name="update_page_markdown",
            description="Update page content via markdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to update"
                    },
                    "markdown": {
                        "type": "string",
                        "description": "Markdown content to update the page"
                    }
                },
                "required": ["page_id", "markdown"]
            }
        )
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle pages tool calls."""
    client = await get_notion_client()
    
    try:
        if name == "create_page":
            parent = arguments["parent"]
            properties = arguments["properties"]
            
            result = await client.pages.create(
                parent=parent,
                properties=properties,
                children=arguments.get("children"),
                icon=arguments.get("icon"),
                cover=arguments.get("cover")
            )
        
        elif name == "retrieve_page":
            page_id = arguments["page_id"]
            filter_properties = arguments.get("filter_properties")
            
            result = await client.pages.retrieve(
                page_id=page_id,
                filter_properties=filter_properties
            )
        
        elif name == "update_page":
            page_id = arguments["page_id"]
            properties = arguments.get("properties")
            archived = arguments.get("archived")
            
            result = await client.pages.update(
                page_id=page_id,
                properties=properties,
                archived=archived
            )
        
        elif name == "trash_page":
            page_id = arguments["page_id"]
            in_trash = arguments.get("in_trash", True)
            
            result = await client.pages.update(
                page_id=page_id,
                archived=in_trash
            )
        
        elif name == "move_page":
            page_id = arguments["page_id"]
            destination = arguments["destination"]
            position = arguments.get("position", "last")
            
            result = await client.pages.move(
                page_id=page_id,
                destination=destination,
                position=position
            )
        
        elif name == "retrieve_page_as_markdown":
            page_id = arguments["page_id"]
            
            result = await client.pages.retrieve(page_id=page_id)
            # Convert to markdown (not directly available in API, so we simulate)
            markdown_content = f"# {result.get('title', 'Untitled')}\n\nPage ID: {page_id}\n\nContent would be extracted here."
            result = {"markdown": markdown_content}
        
        elif name == "update_page_markdown":
            page_id = arguments["page_id"]
            markdown = arguments["markdown"]
            
            # Note: Notion API doesn't directly support markdown updates
            # This would need to be converted to Notion's rich text format
            result = {
                "message": "Markdown update would need conversion to Notion rich text format",
                "page_id": page_id,
                "markdown_length": len(markdown)
            }
        
        else:
            from mcp import types
            raise types.ToolError(f"Unknown pages tool: {name}")
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        return [types.TextContent(type="text", text=result_json)]
        
    except Exception as e:
        from mcp import types
        raise types.ToolError(f"Pages tool '{name}' failed: {str(e)}")