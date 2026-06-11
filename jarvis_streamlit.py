# -*- coding: utf-8 -*-
import streamlit as st
import requests
import subprocess
import json
import os
import sys
import sqlite3
import re
import platform
from pathlib import Path
from datetime import datetime
import time
from dotenv import load_dotenv

# ============================================================
# UTF-8 ENFORCEMENT - منع مشاكل الترميز
# ============================================================
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    try:
        os.system("chcp 65001 > nul")
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except:
        pass

load_dotenv(dotenv_path=Path("D:/JarvisAI/.env"))

# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Jarvis AI - مساعدك الذكي",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ARABIC RTL CSS SUPPORT
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Tajawal:wght@400;500;700;800&display=swap');
    
    * {
        font-family: 'Cairo', 'Tajawal', 'Segoe UI', Tahoma, sans-serif !important;
    }
    
    .main {
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    .jarvis-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 20px;
        text-align: center;
        color: white !important;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .jarvis-header h1 {
        color: white !important;
        font-size: 3em !important;
        font-weight: 900 !important;
        margin: 0 !important;
        unicode-bidi: plaintext !important;
    }
    
    .jarvis-header p {
        color: rgba(255,255,255,0.9) !important;
        font-size: 1.2em !important;
        unicode-bidi: plaintext !important;
    }
    
    .stChatMessage {
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stTextInput input, .stTextArea textarea {
        direction: rtl !important;
        text-align: right !important;
        unicode-bidi: plaintext !important;
    }
    
    [dir="rtl"] {
        font-family: 'Cairo', 'Tajawal', sans-serif !important;
    }
    
    .stat-card {
        background: rgba(255,255,255,0.05);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .stat-number {
        font-size: 2.5em;
        font-weight: 900;
        color: #667eea;
    }
    
    .stat-label {
        color: #e0e0e0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# MULTI-PROVIDER CONFIGURATION
# ============================================================
OLLAMA_URL = "http://localhost:11434/api/chat"
LOCAL_MODEL = "qwen3:8b"

PROVIDERS = {
    "local": {
        "url": OLLAMA_URL,
        "key": "",
        "model": LOCAL_MODEL,
        "name": "Local (Qwen3 8B)"
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", ""),
        "model": "llama-3.3-70b-versatile",
        "name": "Groq (Llama 3.3 70B)"
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "key": os.environ.get("CEREBRAS_API_KEY", ""),
        "model": "llama3.1-70b",
        "name": "Cerebras (Llama 3.1 70B)"
    },
    "sambanova": {
        "url": "https://api.sambanova.ai/v1/chat/completions",
        "key": os.environ.get("SAMBANOVA_API_KEY", ""),
        "model": "Meta-Llama-3.1-405B-Instruct",
        "name": "SambaNova (Llama 3.1 405B)"
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": os.environ.get("OPENROUTER_API_KEY", ""),
        "model": "meta-llama/llama-3.1-70b-instruct",
        "name": "OpenRouter (Multi-Model)"
    },
    "deepseek": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "key": os.environ.get("DEEPSEEK_API_KEY", ""),
        "model": "deepseek-chat",
        "name": "DeepSeek Chat"
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "key": os.environ.get("GEMINI_API_KEY", ""),
        "model": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro"
    }
}

DB_PATH = Path.home() / "jarvis_memory.db"

# ============================================================
# MEMORY & AUDIT LOG SYSTEM
# ============================================================
class Memory:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init_tables()
        
    def _init_tables(self):
        # Conversations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                task TEXT,
                action TEXT,
                result TEXT,
                provider TEXT,
                compressed INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1
            )
        """)
        
        # Projects table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                created_at TEXT
            )
        """)
        
        # Summary table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                id INTEGER PRIMARY KEY,
                content TEXT
            )
        """)
        
        # Audit log table (Append-only)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                actor TEXT,
                action TEXT,
                resource TEXT,
                context TEXT,
                status TEXT,
                error TEXT,
                before_state TEXT,
                after_state TEXT
            )
        """)
        
        # FTS5 for semantic search
        try:
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts 
                USING fts5(task, result, content=conversations, content_rowid=id)
            """)
            self.fts_enabled = True
        except:
            self.fts_enabled = False
            
        self.conn.commit()
    
    def save(self, task, action, result, provider="local", success=1):
        self.conn.execute(
            "INSERT INTO conversations (timestamp, task, action, result, provider, success) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), task, action, result[:500], provider, success)
        )
        
        # Audit log
        self._audit_log("task_execution", action, task, "success" if success else "failed", result[:200])
        
        if self.fts_enabled:
            try:
                lid = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                self.conn.execute(
                    "INSERT INTO memory_fts (rowid, task, result) VALUES (?, ?, ?)",
                    (lid, task, result[:500])
                )
            except:
                pass
        self.conn.commit()
        self.compress_if_needed()
    
    def _audit_log(self, action, resource, context, status, error=""):
        try:
            self.conn.execute(
                """INSERT INTO audit_log 
                   (timestamp, actor, action, resource, context, status, error) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), "jarvis_ai", action, resource, context, status, error)
            )
            self.conn.commit()
        except:
            pass
    
    def compress_if_needed(self):
        c = self.conn.execute("SELECT COUNT(*) FROM conversations WHERE compressed=0").fetchone()[0]
        if c > 10:
            old = self.conn.execute(
                "SELECT task, result FROM conversations WHERE compressed=0 ORDER BY id LIMIT 5"
            ).fetchall()
            if old:
                s = "\n".join([f"- {t[:50]}: {r[:30]}" for t,r in old])
                ex = self.get_summary()
                self.conn.execute(
                    "INSERT OR REPLACE INTO summary (id, content) VALUES (1, ?)",
                    ((ex+"\n"+s)[-2000:],)
                )
                self.conn.execute(
                    "UPDATE conversations SET compressed=1 WHERE id IN (SELECT id FROM conversations WHERE compressed=0 ORDER BY id LIMIT 5)"
                )
                self.conn.commit()
    
    def get_summary(self):
        r = self.conn.execute("SELECT content FROM summary WHERE id=1").fetchone()
        return r[0] if r else ""
    
    def get_recent(self, n=5):
        return self.conn.execute(
            "SELECT task, action, result, provider FROM conversations WHERE compressed=0 ORDER BY id DESC LIMIT ?",
            (n,)
        ).fetchall()
    
    def get_audit_log(self, n=50):
        return self.conn.execute(
            "SELECT timestamp, action, resource, status, error FROM audit_log ORDER BY id DESC LIMIT ?",
            (n,)
        ).fetchall()
    
    def get_success_rate(self):
        r = self.conn.execute("SELECT COUNT(*), SUM(success) FROM conversations").fetchone()
        return round((r[1] or 0)/r[0]*100, 1) if r[0] else 100
    
    def get_total_tasks(self):
        r = self.conn.execute("SELECT COUNT(*) FROM conversations").fetchone()
        return r[0] if r else 0
    
    def save_project(self, name, desc):
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO projects (name, description, created_at) VALUES (?, ?, ?)",
                (name, desc, datetime.now().isoformat())
            )
            self.conn.commit()
            return True
        except:
            return False
    
    def get_projects(self):
        return self.conn.execute(
            "SELECT name, description FROM projects ORDER BY created_at DESC"
        ).fetchall()

memory = Memory()

# ============================================================
# LLM CALLS - SMART PROVIDER SYSTEM
# ============================================================
SYSTEM_PROMPT = """You are Jarvis AI, a Windows automation agent with FULL SYSTEM ACCESS. Return ONLY valid JSON.

CRITICAL: Use DOUBLE backslashes in Windows paths: C:\\\\Users\\\\AL-OFQ\\\\Desktop\\\\file.txt

Available actions:
- write_file: {"path": "...", "content": "..."}
- read_file: {"path": "..."}
- run_cmd: {"cmd": "..."}
- list_files: {"path": "..."}
- remember_project: {"name": "...", "description": "..."}
- recall_projects: {}
- system_info: {}
- registry_read: {"key_path": "HKLM\\\\SOFTWARE\\\\..."}
- registry_write: {"key_path": "...", "value_name": "...", "value_type": "REG_SZ", "value_data": "..."}
- service_control: {"service_name": "wuauserv", "action": "start|stop|restart|status"}
- manage_users: {"action": "list|add|delete|info", "username": "...", "password": "..."}
- environment_variables: {"action": "list|get|set|delete", "var_name": "...", "var_value": "..."}
- scheduled_tasks: {"action": "list|create|delete", "task_name": "...", "command": "...", "time": "14:30"}
- network_config: {"action": "ipconfig|flush_dns|firewall_status", "interface": "..."}
- system_power: {"action": "shutdown|restart|cancel|sleep"}
- power_management: {"action": "high_performance|balanced|status"}

Return ONLY JSON. No explanations."""

def ask_local(prompt, retries=3):
    payload = {
        "model": LOCAL_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 8192}
    }
    for i in range(retries):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=120)
            r.raise_for_status()
            return r.json()["message"]["content"]
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)
            else:
                return None

def ask_cloud(prompt, provider="groq"):
    cfg = PROVIDERS.get(provider)
    if not cfg or not cfg["key"]:
        return None
    
    headers = {
        "Authorization": f"Bearer {cfg['key']}",
        "Content-Type": "application/json"
    }
    
    if provider == "openrouter":
        headers["HTTP-Referer"] = "http://localhost:7860"
        headers["X-Title"] = "Jarvis AI"
    
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 2048
    }
    
    try:
        r = requests.post(cfg["url"], headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except:
        return None

def ask_llm(prompt, preferred_provider=None):
    # Try preferred provider first
    if preferred_provider and preferred_provider != "local":
        r = ask_cloud(prompt, preferred_provider)
        if r:
            return r, preferred_provider
    
    # Try local first (fastest, private)
    r = ask_local(prompt)
    if r:
        return r, "local"
    
    # Fallback to cloud providers in order
    for provider in ["groq", "cerebras", "openrouter", "deepseek", "sambanova", "gemini"]:
        r = ask_cloud(prompt, provider)
        if r:
            return r, provider
    
    return None, None

# ============================================================
# JSON REPAIR & EXTRACTION
# ============================================================
def repair_json(text):
    if not text:
        return text
    s, e = text.find("{"), text.rfind("}") + 1
    if s == -1 or e <= s:
        return text
    text = text[s:e]
    
    # Fix backslashes in paths
    text = re.sub(r'\\\\(?!["\\\\bfnrtu])', r'\\\\\\\\', text)
    # Remove trailing commas
    text = re.sub(r',\\s*}', '}', text)
    text = re.sub(r',\\s*]', ']', text)
    # Fix single quotes
    text = re.sub(r"(?<!\\\\)'", '"', text)
    
    return text

def extract_json(t):
    if not t:
        return None
    
    # Try 1: Direct parse
    try:
        s, e = t.find("{"), t.rfind("}") + 1
        if s != -1 and e > s:
            return json.loads(t[s:e])
    except:
        pass
    
    # Try 2: Repair then parse
    try:
        repaired = repair_json(t)
        return json.loads(repaired)
    except:
        pass
    
    # Try 3: Regex extraction
    try:
        action = re.search(r'"action"\\s*:\\s*"([^"]+)"', t)
        if action:
            result = {"action": action.group(1)}
            for key in ["path", "content", "cmd", "code", "url", "name", "description", "key_path", "value_name", "value_type", "value_data", "service_name", "username", "password", "var_name", "var_value", "task_name", "command", "time", "interface", "action"]:
                m = re.search(rf'"{key}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)"', t)
                if m:
                    val = m.group(1).replace('\\\\n', '\\n').replace('\\\\"', '"')
                    result[key] = val
            if len(result) > 1:
                return result
    except:
        pass
    
    return None

def resolve_placeholders(text):
    if not isinstance(text, str):
        return text
    n = datetime.now()
    text = text.replace("{{CURRENT_DATETIME}}", n.strftime("%Y-%m-%d %H:%M:%S"))
    text = text.replace("{{CURRENT_DATE}}", n.strftime("%Y-%m-%d"))
    text = text.replace("{{CURRENT_TIME}}", n.strftime("%H:%M:%S"))
    text = text.replace("{{USER}}", os.environ.get("USERNAME", "User"))
    text = text.replace("{{DESKTOP}}", str(Path.home() / "Desktop"))
    text = text.replace("{{HOME}}", str(Path.home()))
    return text

# ============================================================
# TOOLS - ENHANCED WITH AUDIT LOGGING
# ============================================================
def write_file(path, content):
    try:
        path = Path(resolve_placeholders(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(resolve_placeholders(content), encoding="utf-8-sig")
        memory._audit_log("write_file", str(path), "File created", "success")
        return f"✅ Written: {path}"
    except Exception as e:
        memory._audit_log("write_file", str(path), "File creation failed", "failed", str(e))
        return f"❌ Error: {e}"

def read_file(path):
    try:
        path = Path(resolve_placeholders(path))
        content = Path(path).read_text(encoding="utf-8-sig")
        memory._audit_log("read_file", str(path), "File read", "success")
        return content
    except Exception as e:
        memory._audit_log("read_file", str(path), "File read failed", "failed", str(e))
        return f"❌ Error: {e}"

def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=120)
        out, err = "", ""
        for enc in ['utf-8', 'cp1256', 'cp437', 'latin1']:
            try:
                out = r.stdout.decode(enc, errors='ignore')
                err = r.stderr.decode(enc, errors='ignore')
                break
            except:
                continue
        result = (out + err).strip() or "✅ Executed"
        memory._audit_log("run_cmd", cmd, "Command executed", "success", result[:100])
        return result
    except Exception as e:
        memory._audit_log("run_cmd", cmd, "Command failed", "failed", str(e))
        return f"❌ Error: {e}"

def list_files(path="."):
    try:
        path = Path(resolve_placeholders(path))
        items = [f"{'📁' if i.is_dir() else '📄'} {i.name}" for i in path.iterdir()]
        result = "\\n".join(items) if items else "Empty"
        memory._audit_log("list_files", str(path), "Directory listed", "success")
        return result
    except Exception as e:
        memory._audit_log("list_files", str(path), "Directory listing failed", "failed", str(e))
        return f"❌ Error: {e}"

def registry_read(key_path):
    try:
        r = subprocess.run(['reg', 'query', key_path], capture_output=True, text=True, timeout=10)
        result = r.stdout if r.returncode == 0 else f"❌ {r.stderr}"
        memory._audit_log("registry_read", key_path, "Registry read", "success" if r.returncode == 0 else "failed")
        return result
    except Exception as e:
        memory._audit_log("registry_read", key_path, "Registry read failed", "failed", str(e))
        return f"❌ Error: {e}"

def registry_write(key_path, value_name, value_type, value_data):
    try:
        r = subprocess.run(
            ['reg', 'add', key_path, '/v', value_name, '/t', value_type, '/d', value_data, '/f'],
            capture_output=True, text=True, timeout=10
        )
        result = f"✅ Registry updated: {key_path}\\\\{value_name}" if r.returncode == 0 else f"❌ {r.stderr}"
        memory._audit_log("registry_write", f"{key_path}\\\\{value_name}", "Registry write", "success" if r.returncode == 0 else "failed")
        return result
    except Exception as e:
        memory._audit_log("registry_write", f"{key_path}\\\\{value_name}", "Registry write failed", "failed", str(e))
        return f"❌ Error: {e}"

def service_control(service_name, action):
    if action not in ['start', 'stop', 'restart', 'status']:
        return f"❌ Invalid action. Use: start, stop, restart, status"
    try:
        if action == 'status':
            r = subprocess.run(['sc', 'query', service_name], capture_output=True, text=True, timeout=10)
        else:
            r = subprocess.run(['net', action, service_name], capture_output=True, text=True, timeout=30)
        result = r.stdout if r.returncode == 0 else f"❌ {r.stderr}"
        memory._audit_log("service_control", service_name, f"Service {action}", "success" if r.returncode == 0 else "failed")
        return result
    except Exception as e:
        memory._audit_log("service_control", service_name, f"Service {action} failed", "failed", str(e))
        return f"❌ Error: {e}"

def manage_users(action, username=None, password=None):
    try:
        if action == 'list':
            r = subprocess.run(['net', 'user'], capture_output=True, text=True, timeout=10)
            result = r.stdout
            memory._audit_log("manage_users", "users", "List users", "success")
            return result
        elif action == 'add' and username and password:
            r = subprocess.run(['net', 'user', username, password, '/add'], capture_output=True, text=True, timeout=10)
            result = f"✅ User '{username}' created" if r.returncode == 0 else f"❌ {r.stderr}"
            memory._audit_log("manage_users", username, f"User {action}", "success" if r.returncode == 0 else "failed")
            return result
        elif action == 'delete' and username:
            r = subprocess.run(['net', 'user', username, '/delete'], capture_output=True, text=True, timeout=10)
            result = f"✅ User '{username}' deleted" if r.returncode == 0 else f"❌ {r.stderr}"
            memory._audit_log("manage_users", username, f"User {action}", "success" if r.returncode == 0 else "failed")
            return result
        elif action == 'info' and username:
            r = subprocess.run(['net', 'user', username], capture_output=True, text=True, timeout=10)
            result = r.stdout
            memory._audit_log("manage_users", username, "User info", "success")
            return result
        return "❌ Invalid action or missing parameters"
    except Exception as e:
        memory._audit_log("manage_users", username or "unknown", f"User {action} failed", "failed", str(e))
        return f"❌ Error: {e}"

def environment_variables(action, var_name=None, var_value=None):
    try:
        if action == 'list':
            result = '\\n'.join([f"{k} = {v}" for k, v in list(os.environ.items())[:50]]) + "\\n... (showing first 50)"
            memory._audit_log("environment_variables", "all", "List env vars", "success")
            return result
        elif action == 'get' and var_name:
            result = f"{var_name} = {os.environ.get(var_name, 'Not set')}"
            memory._audit_log("environment_variables", var_name, "Get env var", "success")
            return result
        elif action == 'set' and var_name and var_value:
            os.environ[var_name] = var_value
            subprocess.run(['setx', var_name, var_value], capture_output=True, timeout=10)
            result = f"✅ {var_name} = {var_value}"
            memory._audit_log("environment_variables", var_name, f"Set env var to {var_value}", "success")
            return result
        elif action == 'delete' and var_name:
            if var_name in os.environ:
                del os.environ[var_name]
            subprocess.run(['reg', 'delete', 'HKCU\\\\Environment', '/v', var_name, '/f'], capture_output=True, timeout=10)
            result = f"✅ {var_name} deleted"
            memory._audit_log("environment_variables", var_name, "Delete env var", "success")
            return result
        return "❌ Invalid action"
    except Exception as e:
        memory._audit_log("environment_variables", var_name or "unknown", f"Env var {action} failed", "failed", str(e))
        return f"❌ Error: {e}"

def scheduled_tasks(action, task_name=None, command=None, time_val=None):
    try:
        if action == 'list':
            r = subprocess.run(['schtasks', '/query', '/fo', 'LIST'], capture_output=True, text=True, timeout=30)
            result = r.stdout[:2000]
            memory._audit_log("scheduled_tasks", "all", "List tasks", "success")
            return result
        elif action == 'create' and task_name and command and time_val:
            r = subprocess.run(
                ['schtasks', '/create', '/tn', task_name, '/tr', command, '/sc', 'once', '/st', time_val],
                capture_output=True, text=True, timeout=10
            )
            result = f"✅ Task '{task_name}' created" if r.returncode == 0 else f"❌ {r.stderr}"
            memory._audit_log("scheduled_tasks", task_name, f"Task created: {command}", "success" if r.returncode == 0 else "failed")
            return result
        elif action == 'delete' and task_name:
            r = subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], capture_output=True, text=True, timeout=10)
            result = f"✅ Task '{task_name}' deleted" if r.returncode == 0 else f"❌ {r.stderr}"
            memory._audit_log("scheduled_tasks", task_name, "Task deleted", "success" if r.returncode == 0 else "failed")
            return result
        return "❌ Invalid action or missing parameters"
    except Exception as e:
        memory._audit_log("scheduled_tasks", task_name or "unknown", f"Task {action} failed", "failed", str(e))
        return f"❌ Error: {e}"

def network_config(action, interface=None):
    try:
        if action == 'ipconfig':
            r = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, timeout=10)
            result = r.stdout
            memory._audit_log("network_config", "all", "IP config", "success")
            return result
        elif action == 'flush_dns':
            r = subprocess.run(['ipconfig', '/flushdns'], capture_output=True, text=True, timeout=10)
            result = r.stdout
            memory._audit_log("network_config", "dns", "Flush DNS", "success")
            return result
        elif action == 'firewall_status':
            r = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], capture_output=True, text=True, timeout=10)
            result = r.stdout[:2000]
            memory._audit_log("network_config", "firewall", "Firewall status", "success")
            return result
        return "❌ Invalid action"
    except Exception as e:
        memory._audit_log("network_config", interface or "unknown", f"Network {action} failed", "failed", str(e))
        return f"❌ Error: {e}"

def system_power(action):
    try:
        if action == 'shutdown':
            subprocess.run(['shutdown', '/s', '/t', '60'], timeout=10)
            memory._audit_log("system_power", "system", "Shutdown initiated", "success")
            return "✅ System will shutdown in 60 seconds. Run 'shutdown /a' to cancel."
        elif action == 'restart':
            subprocess.run(['shutdown', '/r', '/t', '60'], timeout=10)
            memory._audit_log("system_power", "system", "Restart initiated", "success")
            return "✅ System will restart in 60 seconds. Run 'shutdown /a' to cancel."
        elif action == 'cancel':
            subprocess.run(['shutdown', '/a'], timeout=10)
            memory._audit_log("system_power", "system", "Shutdown cancelled", "success")
            return "✅ Shutdown/Restart cancelled"
        elif action == 'sleep':
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], timeout=10)
            memory._audit_log("system_power", "system", "Sleep mode", "success")
            return "✅ System entering sleep mode"
        return "❌ Invalid action"
    except Exception as e:
        memory._audit_log("system_power", "system", f"Power {action} failed", "failed", str(e))
        return f"❌ Error: {e}"

def power_management(action):
    try:
        HIGH_PERF_GUID = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
        BALANCED_GUID = '381b4222-f694-41f0-9685-ff5bb260df2e'
        
        if action == 'high_performance':
            subprocess.run(['powercfg', '/setactive', HIGH_PERF_GUID], capture_output=True, timeout=10)
            subprocess.run(['powercfg', '-change', '-standby-timeout-ac', '0'], capture_output=True, timeout=10)
            subprocess.run(['powercfg', '-change', '-hibernate-timeout-ac', '0'], capture_output=True, timeout=10)
            subprocess.run(['powercfg', '-change', '-monitor-timeout-ac', '0'], capture_output=True, timeout=10)
            memory._audit_log("power_management", "system", "High performance mode", "success")
            return "✅ High Performance mode activated\\n- Sleep: Disabled\\n- Hibernate: Disabled\\n- Monitor timeout: Disabled"
        elif action == 'balanced':
            subprocess.run(['powercfg', '/setactive', BALANCED_GUID], capture_output=True, timeout=10)
            memory._audit_log("power_management", "system", "Balanced mode", "success")
            return "✅ Balanced mode activated"
        elif action == 'status':
            r = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True, timeout=10)
            result = f"Current power plan: {r.stdout.strip()}"
            memory._audit_log("power_management", "system", "Power status check", "success")
            return result
        return "❌ Invalid action"
    except Exception as e:
        memory._audit_log("power_management", "system", f"Power management {action} failed", "failed", str(e))
        return f"❌ Error: {e}"

# ============================================================
# SMART EXECUTION ENGINE
# ============================================================
def verify_result(action, result):
    if not result:
        return False
    rs = str(result).lower()
    
    # Critical failures - don't retry
    if "permission denied" in rs or "no such file" in rs or "access is denied" in rs:
        return False
    
    # Action-specific verification
    if action == "write_file":
        return "written:" in rs or "✅" in rs
    elif action == "read_file":
        return not rs.startswith("❌")
    elif action == "delete_file":
        return "deleted" in rs or "not found" in rs
    elif action == "run_cmd":
        return "❌" not in rs
    elif action == "registry_read":
        return not rs.startswith("❌")
    elif action == "service_control":
        return not rs.startswith("❌")
    
    return True

def execute_single(data, provider="local"):
    action = data.get("action", "none")
    result = ""
    
    try:
        # Basic tools
        if action == "write_file":
            result = write_file(data.get("path", ""), data.get("content", ""))
        elif action == "read_file":
            result = read_file(data.get("path", ""))
        elif action == "run_cmd":
            result = run_cmd(data.get("cmd", ""))
        elif action == "list_files":
            result = list_files(data.get("path", "."))
        
        # Memory tools
        elif action == "remember_project":
            ok = memory.save_project(data.get("name", ""), data.get("description", ""))
            result = f"✅ Project saved: {data.get('name')}" if ok else "❌ Failed"
        elif action == "recall_projects":
            projects = memory.get_projects()
            result = "\\n".join([f"📁 {x[0]}: {x[1]}" for x in projects]) if projects else "لا توجد مشاريع"
        
        # System info
        elif action == "system_info":
            result = f"🖥️ {platform.system()} {platform.release()}\\n👤 {os.environ.get('USERNAME')}\\n📁 {Path.home()}"
        
        # Advanced tools - Registry
        elif action == "registry_read":
            result = registry_read(data.get("key_path", ""))
        elif action == "registry_write":
            result = registry_write(
                data.get("key_path", ""),
                data.get("value_name", ""),
                data.get("value_type", "REG_SZ"),
                data.get("value_data", "")
            )
        
        # Advanced tools - Services
        elif action == "service_control":
            result = service_control(data.get("service_name", ""), data.get("action", "status"))
        
        # Advanced tools - Users
        elif action == "manage_users":
            result = manage_users(
                data.get("action", "list"),
                data.get("username"),
                data.get("password")
            )
        
        # Advanced tools - Environment
        elif action == "environment_variables":
            result = environment_variables(
                data.get("action", "list"),
                data.get("var_name"),
                data.get("var_value")
            )
        
        # Advanced tools - Scheduled Tasks
        elif action == "scheduled_tasks":
            result = scheduled_tasks(
                data.get("action", "list"),
                data.get("task_name"),
                data.get("command"),
                data.get("time")
            )
        
        # Advanced tools - Network
        elif action == "network_config":
            result = network_config(data.get("action", "ipconfig"), data.get("interface"))
        
        # Advanced tools - Power
        elif action == "system_power":
            result = system_power(data.get("action"))
        elif action == "power_management":
            result = power_management(data.get("action"))
        
        else:
            result = f"❌ Unknown action: {action}"
    
    except Exception as e:
        result = f"❌ Error: {e}"
    
    return result, action, verify_result(action, result)

def execute(task, preferred_provider=None):
    ctx = memory.get_summary()
    recent = memory.get_recent(3)
    
    prompt = f"""Task: {task}
Context: {ctx}
Recent: {', '.join([r[0][:40] for r in recent])}

Return ONLY valid JSON."""
    
    resp, provider = ask_llm(prompt, preferred_provider)
    
    if not resp:
        return "❌ No response from any model. Check if Ollama is running or API keys are set.", "none", False
    
    data = extract_json(resp)
    
    if not data:
        return f"❌ Invalid JSON response:\\n{resp[:300]}", "error", False
    
    if "action" not in data:
        return f"⚠️ JSON missing 'action' field. Parsed: {data}", "error", False
    
    result, action, verified = execute_single(data, provider)
    memory.save(task, action, result, provider, 1 if verified else 0)
    
    return result, action, verified

# ============================================================
# STREAMLIT UI
# ============================================================
st.markdown('''
<div class="jarvis-header">
    <h1>🤖 Jarvis AI</h1>
    <p>مساعدك الذكي الشامل لأتمتة Windows</p>
</div>
''', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📊 الإحصائيات")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("المهام", memory.get_total_tasks())
    with col2:
        st.metric("النجاح", f"{memory.get_success_rate()}%")
    
    st.markdown("---")
    st.markdown("### 🔧 الحالة")
    
    # Check Ollama
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        ollama_status = "🟢 متصل" if r.status_code == 200 else "🔴 غير متصل"
    except:
        ollama_status = "🔴 غير متصل"
    
    st.markdown(f"**Ollama:** {ollama_status}")
    st.markdown(f"**Groq:** {'🟢 متاح' if PROVIDERS['groq']['key'] else '🔴 غير مُعد'}")
    
    st.markdown("---")
    st.markdown("### 🎯 النموذج المفضل")
    provider_choice = st.selectbox(
        "اختر النموذج",
        ["auto"] + [p["name"] for p in PROVIDERS.values() if p["key"] or p["name"].startswith("Local")],
        index=0
    )
    
    st.markdown("---")
    if st.button("🗑️ مسح المحادثة", key="btn_1_🗑️_مسح_المحادثة"):
        st.session_state.messages = []
        st.rerun()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 المحادثة", "📜 السجل", "📁 المشاريع", "🔍 سجل التدقيق"])

# Tab 1: Chat
with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 مرحباً! أنا Jarvis، مساعدك الذكي. كيف يمكنني مساعدتك اليوم؟"}
        ]
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("اكتب مهمتك هنا..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("⏳ جاري التفكير والتنفيذ..."):
                result, action, verified = execute(prompt, provider_choice if provider_choice != "auto" else None)
                status = "✅" if verified else "⚠️"
                response = f"{status} **{action}**\\n\\n{result}"
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

# Tab 2: History
with tab2:
    st.markdown("### 📜 سجل المهام والذاكرة الذكية")
    
    if st.button("🔄 تحديث السجل", key="btn_1_🔄_تحديث_السجل"):
        st.rerun()
    
    summary = memory.get_summary()
    if summary:
        st.markdown("#### 🧠 ملخص الذاكرة المضغوطة")
        st.info(summary)
    
    st.markdown("#### 🕐 آخر 20 مهمة")
    recent = memory.get_recent(20)
    if recent:
        for r in recent:
            with st.expander(f"**{r[1]}** - {r[0][:80]}"):
                st.code(r[2], language="text")
                st.caption(f"النموذج: {r[3]}")
    else:
        st.info("لا توجد مهام بعد")

# Tab 3: Projects
with tab3:
    st.markdown("### 📁 المشاريع المحفوظة")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_kw = st.text_input("🔍 بحث في المشاريع")
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 تحديث", key="btn_1_🔄_تحديث"):
            st.rerun()
    
    projects = memory.get_projects()
    if search_kw:
        projects = [p for p in projects if search_kw.lower() in p[0].lower() or search_kw.lower() in p[1].lower()]
    
    if projects:
        for p in projects:
            with st.container():
                st.markdown(f"#### 📁 {p[0]}")
                st.markdown(p[1])
                st.markdown("---")
    else:
        st.info("لا توجد مشاريع محفوظة. جرب: احفظ مشروع X بوصف Y")

# Tab 4: Audit Log
with tab4:
    st.markdown("### 🔍 سجل التدقيق الآلي")
    st.markdown("سجل غير قابل للتعديل لجميع العمليات")
    
    if st.button("🔄 تحديث السجل", key="btn_2_🔄_تحديث_السجل"):
        st.rerun()
    
    audit_logs = memory.get_audit_log(50)
    if audit_logs:
        for log in audit_logs:
            timestamp, action, resource, status, error = log
            status_icon = "✅" if status == "success" else "❌"
            with st.expander(f"{status_icon} **{action}** - {resource} ({timestamp})"):
                st.caption(f"الحالة: {status}")
                if error:
                    st.error(f"الخطأ: {error}")
    else:
        st.info("لا توجد سجلات تدقيق بعد")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; padding: 20px;">
    <p>🤖 <strong>Jarvis AI - Ultra Edition</strong></p>
    <p style="font-size: 0.85em;">
        Powered by Ollama + Groq + Multi-Provider | 🔒 Audit Logging | 🌐 Arabic RTL
    </p>
</div>
""", unsafe_allow_html=True)
