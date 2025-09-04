"""Type definitions for YouTrack API."""

from typing import Any

# For JSON API responses we need Any due to dynamic nature
type JSONDict = dict[str, Any]
type JSONList = list[Any]
type JSONValue = Any

# Field types for YouTrack custom fields
type FieldValue = Any
type FieldInfo = dict[str, Any]
type FieldTypes = dict[str, FieldInfo]

# Issue and project data types
type IssueData = dict[str, Any]
type ProjectData = dict[str, Any]
type UserData = dict[str, Any]
type CommentData = dict[str, Any]
type CustomFieldData = dict[str, Any]

# Query parameters - accept various param types
type QueryParams = dict[str, Any]

# Tool definition types
type ToolDefinition = dict[str, Any]  # Contains function, description, etc.
type ToolRegistry = dict[str, Any]  # More flexible to handle various tool formats

# Protocol for tool instances - more flexible
type ToolInstance = Any  # Tool class instances

# MCP Tool Parameter types
type ParamType = str  # "string", "number", "boolean", "object", "array"

# Parameter definition for MCP tools
class ParameterDefinition:
    def __init__(
        self,
        param_type: ParamType = "string",
        description: str = "",
        required: bool = True,
        default: Any = None,
        enum: list[Any] | None = None
    ):
        self.type = param_type
        self.description = description
        self.required = required
        self.default = default
        self.enum = enum

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP parameter schema format."""
        result: dict[str, Any] = {
            "type": self.type,
            "description": self.description
        }
        if self.enum is not None:
            result["enum"] = self.enum
        if not self.required and self.default is not None:
            result["default"] = self.default
        return result
