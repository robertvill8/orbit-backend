"""
Tool definitions for Claude API function calling.
Defines available tools and their JSON schemas.
"""

# Tool definitions matching Claude's tool use format
TOOL_DEFINITIONS = [
    {
        "name": "create_task",
        "description": """Create a new task with title, description, priority, and optional due date.
        Use this when the user asks you to remember something, create a todo, or schedule a task.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Clear, concise task title"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed task description (optional)"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority level",
                    "default": "medium"
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in ISO 8601 format (YYYY-MM-DD) if mentioned by user",
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "search_email",
        "description": """Search through the user's emails by keywords or date range.
        Use this when the user asks about emails, wants to find specific messages, or check their inbox.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (keywords, sender name, subject)"
                },
                "from_date": {
                    "type": "string",
                    "description": "Start date for search range (ISO 8601 format: YYYY-MM-DD)"
                },
                "to_date": {
                    "type": "string",
                    "description": "End date for search range (ISO 8601 format: YYYY-MM-DD)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_calendar_event",
        "description": """Create a calendar event with title, date, time, and optional attendees.
        Use this when the user wants to schedule a meeting, set an appointment, or add an event to their calendar.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title"
                },
                "start_time": {
                    "type": "string",
                    "description": "Event start time (ISO 8601 datetime format)"
                },
                "end_time": {
                    "type": "string",
                    "description": "Event end time (ISO 8601 datetime format)"
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email addresses"
                }
            },
            "required": ["title", "start_time", "end_time"]
        }
    },
    {
        "name": "extract_document_text",
        "description": """Extract text from a document using OCR.
        Use this when the user uploads a document and wants to extract its content.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_path": {
                    "type": "string",
                    "description": "Path to the document file"
                }
            },
            "required": ["document_path"]
        }
    }
]


def get_tool_by_name(name: str) -> dict:
    """
    Get tool definition by name.

    Args:
        name: Tool name

    Returns:
        Tool definition dict

    Raises:
        ValueError: If tool not found
    """
    for tool in TOOL_DEFINITIONS:
        if tool["name"] == name:
            return tool
    raise ValueError(f"Tool not found: {name}")
