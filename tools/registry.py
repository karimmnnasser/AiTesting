"""Tool Registry - supports both classes and functions"""
from typing import Dict, Any, Optional, Callable

TOOLS: Dict[str, Any] = {}

DANGEROUS_TOOLS = {
    "run_cmd", "registry_write", "registry_delete",
    "manage_users", "system_power", "service_control",
    "scheduled_tasks", "kill_process", "network_config",
    "environment_variables",
}


def register_tool(name_or_class=None):
    """Decorator that works with classes, functions, and custom names."""
    if name_or_class is not None and not isinstance(name_or_class, str):
        if callable(name_or_class):
            tool_name = getattr(name_or_class, 'name', name_or_class.__name__.lower())
            TOOLS[tool_name] = name_or_class
            return name_or_class
        raise TypeError(f"Invalid: {name_or_class}")
    
    if isinstance(name_or_class, str):
        def decorator(cls_or_func):
            TOOLS[name_or_class] = cls_or_func
            return cls_or_func
        return decorator
    
    def decorator(cls_or_func):
        if callable(cls_or_func):
            tool_name = getattr(cls_or_func, 'name', cls_or_func.__name__.lower())
            TOOLS[tool_name] = cls_or_func
        return cls_or_func
    return decorator


def get_tool(name: str) -> Optional[Any]:
    return TOOLS.get(name)


def requires_confirmation(action: str) -> bool:
    return action in DANGEROUS_TOOLS


def list_tools() -> Dict[str, Any]:
    return TOOLS.copy()


def execute_tool(name: str, **kwargs) -> Any:
    tool = get_tool(name)
    if not tool:
        raise ValueError(f"Unknown tool: {name}")
    if callable(tool):
        return tool(**kwargs)
    if hasattr(tool, 'execute'):
        return tool.execute(**kwargs)
    raise TypeError(f"Tool {name} not callable")
