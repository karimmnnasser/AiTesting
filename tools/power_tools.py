from tools.registry import register_tool
import subprocess

@register_tool("system_power")
def system_power(action):
    try:
        if action == 'shutdown':
            subprocess.run(['shutdown', '/s', '/t', '60'], timeout=10)
            return "System will shutdown in 60 seconds. Use 'shutdown /a' to cancel"
        elif action == 'restart':
            subprocess.run(['shutdown', '/r', '/t', '60'], timeout=10)
            return "System will restart in 60 seconds"
        elif action == 'cancel':
            subprocess.run(['shutdown', '/a'], timeout=10)
            return "Shutdown cancelled"
        elif action == 'sleep':
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], timeout=10)
            return "Entering sleep mode"
        return "Invalid action"
    except Exception as e:
        return f"Error: {e}"

@register_tool("power_management")
def power_management(action):
    try:
        HIGH_PERF = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
        BALANCED = '381b4222-f694-41f0-9685-ff5bb260df2e'
        if action == 'high_performance':
            subprocess.run(['powercfg', '/setactive', HIGH_PERF], capture_output=True, timeout=10)
            return "High Performance mode activated"
        elif action == 'balanced':
            subprocess.run(['powercfg', '/setactive', BALANCED], capture_output=True, timeout=10)
            return "Balanced mode activated"
        elif action == 'status':
            r = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True, timeout=10)
            return r.stdout.strip()
        return "Invalid action"
    except Exception as e:
        return f"Error: {e}"
