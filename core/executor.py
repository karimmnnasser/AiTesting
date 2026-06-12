"""Executor - handles tool execution safely"""
from schemas.tool_schema import ToolRequest, ToolResponse
from tools.registry import get_tool, requires_confirmation, execute_tool


class Executor:
    def execute(self, request: ToolRequest) -> ToolResponse:
        try:
            tool = get_tool(request.action)
            if not tool:
                return ToolResponse.fail(request.action, f"Unknown tool: {request.action}")
            
            if requires_confirmation(request.action):
                return ToolResponse.needs_confirmation(request.action, request.parameters)
            
            result = execute_tool(request.action, **request.parameters)
            return ToolResponse.ok(request.action, data=result)
        except Exception as e:
            return ToolResponse.fail(request.action, str(e))
