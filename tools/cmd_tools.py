import subprocess
import sys
from tools.base import BaseTool
from tools.registry import register_tool
from schemas.tool_schema import ToolRequest, ToolResponse

@register_tool
class RunCmdTool(BaseTool):
    name = "run_cmd"
    description = "Run a system command"
    dangerous = False  # نعم، يمكن أن تكون خطيرة لكننا سنطلب تأكيد لاحقاً

    def execute(self, request: ToolRequest) -> ToolResponse:
        cmd = request.parameters.get("cmd", "")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=120)
            # محاولة فك الترميز بعدة طرق
            out, err = "", ""
            for enc in ['utf-8', 'cp1256', 'cp437', 'latin1']:
                try:
                    out = result.stdout.decode(enc, errors='ignore')
                    err = result.stderr.decode(enc, errors='ignore')
                    break
                except:
                    continue
            output = (out + err).strip()
            if not output:
                output = "Executed (no output)"
            return ToolResponse(success=True, message=output)
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")

@register_tool
class RunPythonTool(BaseTool):
    name = "run_python"
    description = "Execute Python code"
    dangerous = False

    def execute(self, request: ToolRequest) -> ToolResponse:
        code = request.parameters.get("code", "")
        try:
            result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=30)
            out = result.stdout.decode('utf-8', errors='ignore')
            err = result.stderr.decode('utf-8', errors='ignore')
            output = (out + err).strip()
            if not output:
                output = "Executed (no output)"
            return ToolResponse(success=True, message=output)
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")
