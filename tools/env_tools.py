from tools.registry import register_tool
import os
import subprocess

@register_tool("environment_variables")
def environment_variables(action, var_name=None, var_value=None):
    try:
        if action == 'list':
            return "\n".join([f"{k}={v}" for k, v in list(os.environ.items())[:50]])
        elif action == 'get' and var_name:
            return f"{var_name}={os.environ.get(var_name, 'Not set')}"
        elif action == 'set' and var_name and var_value:
            os.environ[var_name] = var_value
            subprocess.run(['setx', var_name, var_value], capture_output=True, timeout=10)
            return f"Set {var_name}={var_value}"
        elif action == 'delete' and var_name:
            if var_name in os.environ:
                del os.environ[var_name]
            subprocess.run(['reg', 'delete', 'HKCU\\Environment', '/v', var_name, '/f'], capture_output=True, timeout=10)
            return f"Deleted {var_name}"
        return "Invalid action"
    except Exception as e:
        return f"Error: {e}"
