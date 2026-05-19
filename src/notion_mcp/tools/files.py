"""
File Uploads tools for Notion MCP server.
"""

import json
import base64
import mimetypes
import os
from typing import Any, Dict, Optional

import mcp
from mcp import types

# client is passed in from server.py


async def list_tools() -> list[types.Tool]:
    """List available files tools."""
    return [
        # Create File Upload
        types.Tool(
            name="create_file_upload",
            description="Initiate a file upload to Notion",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the file"
                    },
                    "size": {
                        "type": "integer",
                        "description": "Size of the file in bytes"
                    },
                    "type": {
                        "type": "string",
                        "description": "MIME type of the file"
                    }
                },
                "required": ["name", "size", "type"]
            }
        ),
        
        # Send File Upload Data
        types.Tool(
            name="send_file_upload",
            description="Send file data to complete the upload",
            inputSchema={
                "type": "object",
                "properties": {
                    "upload_id": {
                        "type": "string",
                        "description": "The ID from the create upload response"
                    },
                    "data": {
                        "type": "string",
                        "description": "Base64 encoded file data"
                    }
                },
                "required": ["upload_id", "data"]
            }
        ),
        
        # Complete File Upload
        types.Tool(
            name="complete_file_upload",
            description="Finalize the file upload",
            inputSchema={
                "type": "object",
                "properties": {
                    "upload_id": {
                        "type": "string",
                        "description": "The ID from the create upload response"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Final file name"
                    }
                },
                "required": ["upload_id", "file_name"]
            }
        ),
        
        # List File Uploads
        types.Tool(
            name="list_file_uploads",
            description="List file uploads in the workspace",
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
                        "description": "Optional filter criteria"
                    }
                }
            }
        ),
        
        # Retrieve File Upload
        types.Tool(
            name="retrieve_file_upload",
            description="Retrieve a specific file upload status",
            inputSchema={
                "type": "object",
                "properties": {
                    "upload_id": {
                        "type": "string",
                        "description": "The ID of the file upload to retrieve"
                    }
                },
                "required": ["upload_id"]
            }
        )
    ]


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle files tool calls."""
    client = await get_notion_client()
    
    try:
        if name == "create_file_upload":
            filename = arguments["name"]
            size = arguments["size"]
            file_type = arguments["type"]
            
            result = await client.file_uploads.create(
                name=filename,
                size=size,
                type=file_type
            )
        
        elif name == "send_file_upload":
            upload_id = arguments["upload_id"]
            data = arguments["data"]
            
            # Note: Notion file uploads typically work in chunks, but this is simplified
            # In a real implementation, you'd need to handle chunking and progress tracking
            result = await client.file_uploads.send(
                upload_id=upload_id,
                data=data
            )
        
        elif name == "complete_file_upload":
            upload_id = arguments["upload_id"]
            file_name = arguments["file_name"]
            
            result = await client.file_uploads.complete(
                upload_id=upload_id,
                file_name=file_name
            )
        
        elif name == "list_file_uploads":
            page_size = arguments.get("page_size", 20)
            start_cursor = arguments.get("start_cursor")
            filter_criteria = arguments.get("filter")
            
            # Build list parameters
            list_params = {"page_size": min(page_size, 100)}
            
            if start_cursor:
                list_params["start_cursor"] = start_cursor
            if filter_criteria:
                list_params["filter"] = filter_criteria
            
            result = await client.file_uploads.list(**list_params)
        
        elif name == "retrieve_file_upload":
            upload_id = arguments["upload_id"]
            
            result = await client.file_uploads.retrieve(upload_id=upload_id)
        
        else:
            from mcp import types
            raise types.ToolError(f"Unknown files tool: {name}")
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        return [types.TextContent(type="text", text=result_json)]
        
    except Exception as e:
        from mcp import types
        raise types.ToolError(f"Files tool '{name}' failed: {str(e)}")


def encode_file_to_base64(file_path: str) -> str:
    """Encode a file to base64 string."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def detect_mime_type(file_path: str) -> str:
    """Detect MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)