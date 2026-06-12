from pathlib import Path
from tools.base import BaseTool
from tools.registry import register_tool
from schemas.tool_schema import ToolRequest, ToolResponse

@register_tool
class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file"
    dangerous = False

    def execute(self, request: ToolRequest) -> ToolResponse:
        path = request.parameters.get("path", "")
        content = request.parameters.get("content", "")
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return ToolResponse(success=True, message=f"Written: {p}")
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")

@register_tool
class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read content from a file"
    dangerous = False

    def execute(self, request: ToolRequest) -> ToolResponse:
        path = request.parameters.get("path", "")
        try:
            content = Path(path).read_text(encoding="utf-8")
            return ToolResponse(success=True, message=content)
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")

@register_tool
class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files in a directory"
    dangerous = False

    def execute(self, request: ToolRequest) -> ToolResponse:
        path = request.parameters.get("path", ".")
        try:
            p = Path(path)
            items = [f"{'[DIR]' if i.is_dir() else '[FILE]'} {i.name}" for i in p.iterdir()]
            result = "\n".join(items) if items else "Empty folder"
            return ToolResponse(success=True, message=result)
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")

@register_tool
class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file"
    dangerous = False

    def execute(self, request: ToolRequest) -> ToolResponse:
        path = request.parameters.get("path", "")
        try:
            p = Path(path)
            if p.exists():
                p.unlink()
                return ToolResponse(success=True, message=f"Deleted: {p}")
            else:
                return ToolResponse(success=False, message="File not found")
        except Exception as e:
            return ToolResponse(success=False, message=f"Error: {e}")
