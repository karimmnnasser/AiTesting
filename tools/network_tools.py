from tools.registry import register_tool
import subprocess

@register_tool("network_config")
def network_config(action, interface=None):
    try:
        if action == 'ipconfig':
            r = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, timeout=10)
            return r.stdout
        elif action == 'flush_dns':
            r = subprocess.run(['ipconfig', '/flushdns'], capture_output=True, text=True, timeout=10)
            return r.stdout
        elif action == 'firewall_status':
            r = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], capture_output=True, text=True, timeout=10)
            return r.stdout[:2000]
        return "Invalid action"
    except Exception as e:
        return f"Error: {e}"
