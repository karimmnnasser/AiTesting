"""Constants - الثوابت العامة للمشروع"""
from pathlib import Path
from typing import Set

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = Path.home() / "jarvis_memory.db"

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_LOCAL_MODEL = "qwen3:8b"
OLLAMA_TIMEOUT = 120

DEFAULT_PROVIDER = "groq"
CLOUD_TIMEOUT = 60

MAX_RETRIES = 3
MAX_CONTEXT_LENGTH = 8192
MAX_TOKENS = 2048
MAX_HISTORY_LENGTH = 20

SERVER_PORT = 7860
SERVER_ADDRESS = "localhost"

SUCCESS_ICON = "✅"
ERROR_ICON = "❌"
WARNING_ICON = "⚠️"
INFO_ICON = "ℹ️"

ALLOWED_TOOLS: Set[str] = {
    "write_file", "read_file", "list_files", "delete_file", "copy_file", "move_file",
    "run_cmd", "system_info", "get_processes", "kill_process",
    "registry_read", "registry_write", "registry_delete",
    "service_control", "get_services",
    "manage_users",
    "network_config", "ping", "get_network_info",
    "system_power", "power_management",
    "scheduled_tasks",
    "environment_variables",
    "remember_project", "recall_projects",
}

DANGEROUS_TOOLS: Set[str] = {
    "run_cmd", "registry_write", "registry_delete",
    "manage_users", "system_power", "service_control",
    "scheduled_tasks", "kill_process",
}

SYSTEM_PROMPT = """أنت Jarvis AI، مساعد ذكي لأتمتة Windows.

قواعد صارمة:
1. أرجع JSON واحد فقط بصيغة: {"action": "...", "parameters": {...}}
2. لا ترجع قائمة أوامر، فقط أمر واحد في كل مرة
3. لا ترجع حقول مثل "errors" أو "recent_tasks" أو "actions"
4. استخدم المسارات الكاملة مع double backslash: C:\\Users\\AL-OFQ\\Desktop\\file.txt

الأوامر المتاحة:
- write_file: {"action": "write_file", "parameters": {"path": "...", "content": "..."}}
- read_file: {"action": "read_file", "parameters": {"path": "..."}}
- run_cmd: {"action": "run_cmd", "parameters": {"cmd": "..."}}
- list_files: {"action": "list_files", "parameters": {"path": "..."}}
- system_info: {"action": "system_info", "parameters": {}}

مثال صحيح:
{"action": "write_file", "parameters": {"path": "C:\\test.txt", "content": "hello"}}

نفذ أمر واحد فقط الآن:"""
