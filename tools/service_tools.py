import subprocess
from tools.base import BaseTool
from tools.registry import register_tool
from schemas.tool_schema import ToolRequest, ToolResponse

@register_tool
class ServiceControlTool(BaseTool):
    name = "service_control"
    description = "Start, stop, restart, or get status of a Windows service"
    dangerous = True

    def execute(self, request: ToolRequest) -> ToolResponse:
        service_name = request.parameters.get("service_name", "")
        action = request.parameters.get("action", "status")
        valid_actions = ['start', 'stop', 'restart', 'status']
        if action not in valid_actions:
            return ToolResponse(success=False, message=f"Invalid action. Use: {', '.join(valid_actions)}")
        try:
            if action == 'status':
                r = subprocess.run(['sc', 'query', service_name], capture_output=True, text=True, timeout=10)
            else:
                r = subprocess.run(['net', action, service_name], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return ToolResponse(success=True, message=r.stdout)
            else:
                return ToolResponse(success=False, message=f"Error: {r.stderr}")
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")
