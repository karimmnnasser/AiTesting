from tools.registry import register_tool
import subprocess

@register_tool("scheduled_tasks")
def scheduled_tasks(action, task_name=None, command=None, time_val=None):
    try:
        if action == 'list':
            r = subprocess.run(['schtasks', '/query', '/fo', 'LIST'], capture_output=True, text=True, timeout=30)
            return r.stdout[:2000]
        elif action == 'create' and task_name and command and time_val:
            r = subprocess.run(
                ['schtasks', '/create', '/tn', task_name, '/tr', command, '/sc', 'once', '/st', time_val],
                capture_output=True, text=True, timeout=10
            )
            return f"Task '{task_name}' created" if r.returncode == 0 else f"Error: {r.stderr}"
        elif action == 'delete' and task_name:
            r = subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], capture_output=True, text=True, timeout=10)
            return f"Task '{task_name}' deleted" if r.returncode == 0 else f"Error: {r.stderr}"
        return "Invalid action"
    except Exception as e:
        return f"Error: {e}"
