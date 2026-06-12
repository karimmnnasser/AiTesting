import subprocess
from tools.base import BaseTool
from tools.registry import register_tool
from schemas.tool_schema import ToolRequest, ToolResponse

@register_tool
class ManageUsersTool(BaseTool):
    name = "manage_users"
    description = "Manage Windows users: list, add, delete, info"
    dangerous = True

    def execute(self, request: ToolRequest) -> ToolResponse:
        action = request.parameters.get("action", "list")
        username = request.parameters.get("username", "")
        password = request.parameters.get("password", "")
        try:
            if action == "list":
                r = subprocess.run(['net', 'user'], capture_output=True, text=True, timeout=10)
                return ToolResponse(success=True, message=r.stdout)
            elif action == "add" and username and password:
                r = subprocess.run(['net', 'user', username, password, '/add'], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    return ToolResponse(success=True, message=f"User '{username}' created")
                else:
                    return ToolResponse(success=False, message=f"Error: {r.stderr}")
            elif action == "delete" and username:
                r = subprocess.run(['net', 'user', username, '/delete'], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    return ToolResponse(success=True, message=f"User '{username}' deleted")
                else:
                    return ToolResponse(success=False, message=f"Error: {r.stderr}")
            elif action == "info" and username:
                r = subprocess.run(['net', 'user', username], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    return ToolResponse(success=True, message=r.stdout)
                else:
                    return ToolResponse(success=False, message=f"Error: {r.stderr}")
            else:
                return ToolResponse(success=False, message="Invalid action or missing parameters")
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")
