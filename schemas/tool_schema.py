from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ToolRequest(BaseModel):
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ToolResponse(BaseModel):
    success: bool
    message: str = ""
    needs_confirmation: bool = False

class LLMResponse(BaseModel):
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    raw_text: Optional[str] = None

    @classmethod
    def from_action(cls, action: str, parameters: Dict[str, Any] = None):
        """Create LLMResponse directly from action and parameters (for testing)."""
        return cls(
            action=action,
            parameters=parameters or {},
            raw_text=None
        )
