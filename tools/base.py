from abc import ABC, abstractmethod
from schemas.tool_schema import ToolRequest, ToolResponse

class BaseTool(ABC):
    """Base class for all Jarvis tools."""
    
    name: str = ""
    description: str = ""
    dangerous: bool = False
    
    @abstractmethod
    def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute the tool with given request."""
        pass
