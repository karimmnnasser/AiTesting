"""Executor - handles tool execution safely"""
from schemas.tool_schema import ToolRequest, ToolResponse
from tools.registry import get_tool, requires_confirmation, execute_tool


class Executor:
    def execute(self, request: ToolRequest, confirmed: bool = False) -> ToolResponse:
        try:
            tool = get_tool(request.action)
            if not tool:
                return ToolResponse.fail(request.action, f"Unknown tool: {request.action}")
            
            if requires_confirmation(request.action) and not confirmed:
                return ToolResponse.needs_confirmation_response(request.action, request.parameters)
            
            result = execute_tool(request.action, request=request)
            if isinstance(result, ToolResponse):
                if result.action is None:
                    result.action = request.action
                if result.data is None and result.message:
                    result.data = result.message
                if result.error is None and not result.success:
                    result.error = result.message
                return result

            return ToolResponse.ok(request.action, data=result)
        except Exception as e:
            return ToolResponse.fail(request.action, str(e))
