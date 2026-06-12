from tools.base import BaseTool
from tools.registry import register_tool
from schemas.tool_schema import ToolRequest, ToolResponse
import subprocess

@register_tool
class SystemPowerTool(BaseTool):
    name = "system_power"
    description = "Control system power (shutdown, restart, sleep, cancel)"
    dangerous = True

    def execute(self, request: ToolRequest) -> ToolResponse:
        action = request.parameters.get("action", "")
        try:
            if action == "shutdown":
                subprocess.run(['shutdown', '/s', '/t', '60'], timeout=10)
                return ToolResponse(success=True, message="System will shutdown in 60 seconds. Use 'shutdown /a' to cancel.")
            elif action == "restart":
                subprocess.run(['shutdown', '/r', '/t', '60'], timeout=10)
                return ToolResponse(success=True, message="System will restart in 60 seconds.")
            elif action == "cancel":
                subprocess.run(['shutdown', '/a'], timeout=10)
                return ToolResponse(success=True, message="Shutdown cancelled.")
            elif action == "sleep":
                subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], timeout=10)
                return ToolResponse(success=True, message="Entering sleep mode.")
            else:
                return ToolResponse(success=False, message=f"Unknown power action: {action}")
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")
