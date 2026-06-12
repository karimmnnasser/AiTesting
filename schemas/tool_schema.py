from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ToolRequest(BaseModel):
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ToolResponse(BaseModel):
    success: bool
    message: str = ""
    action: Optional[str] = None
    data: Any = None
    error: Optional[str] = None
    needs_confirmation: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, action: str, data: Any = None, message: str = ""):
        text = message if message else ("" if data is None else str(data))
        return cls(success=True, action=action, data=data, message=text)

    @classmethod
    def fail(cls, action: str, error: str):
        return cls(success=False, action=action, error=error, message=error)

    @classmethod
    def needs_confirmation_response(cls, action: str, parameters: Dict[str, Any] = None):
        params = parameters or {}
        return cls(
            success=False,
            action=action,
            data=params,
            message=f"Tool requires confirmation: {action}",
            needs_confirmation=True,
            parameters=params,
        )

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
