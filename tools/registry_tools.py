import subprocess
from tools.base import BaseTool
from tools.registry import register_tool
from schemas.tool_schema import ToolRequest, ToolResponse

@register_tool
class RegistryReadTool(BaseTool):
    name = "registry_read"
    description = "Read Windows registry value"
    dangerous = False

    def execute(self, request: ToolRequest) -> ToolResponse:
        key_path = request.parameters.get("key_path", "")
        try:
            r = subprocess.run(['reg', 'query', key_path], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return ToolResponse(success=True, message=r.stdout)
            else:
                return ToolResponse(success=False, message=f"Error: {r.stderr}")
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")

@register_tool
class RegistryWriteTool(BaseTool):
    name = "registry_write"
    description = "Write Windows registry value"
    dangerous = True

    def execute(self, request: ToolRequest) -> ToolResponse:
        key_path = request.parameters.get("key_path", "")
        value_name = request.parameters.get("value_name", "")
        value_type = request.parameters.get("value_type", "REG_SZ")
        value_data = request.parameters.get("value_data", "")
        try:
            r = subprocess.run(
                ['reg', 'add', key_path, '/v', value_name, '/t', value_type, '/d', value_data, '/f'],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                return ToolResponse(success=True, message=f"Registry updated: {key_path}\\{value_name}")
            else:
                return ToolResponse(success=False, message=f"Error: {r.stderr}")
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")
