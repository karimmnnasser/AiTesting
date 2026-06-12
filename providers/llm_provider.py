# -*- coding: utf-8 -*-
"""LLM provider integration for Groq and local Ollama models."""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path("D:/JarvisAI/.env"))

OLLAMA_URL = "http://localhost:11434/api/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

LOCAL_MODELS = {
    "qwen3:8b": "Qwen3 8B",
    "deepseek-coder-v2:16b": "DeepSeek Coder 16B",
    "qwen2.5:7b-instruct": "Qwen2.5 Instruct",
    "llama3.1:8b": "Llama 3.1 8B",
    "qwen2.5-coder:7b": "Qwen Coder 7B",
    "qwen2.5vl:7b": "Qwen2.5 VL 7B",
}

DEFAULT_LOCAL_MODEL = "qwen3:8b"

SYSTEM_PROMPT = """You are Jarvis AI, a Windows automation assistant.

CRITICAL RULES:
1. For technical tasks (create file, run command, list files, read files, system info, registry, services, network, users, power), respond with ONLY valid JSON.
2. For general conversation, respond naturally in Arabic without JSON.
3. Return one action only.

JSON format:
{"action": "tool_name", "parameters": {"param1": "value1"}}

Available tools:
- write_file: {"action": "write_file", "parameters": {"path": "file.txt", "content": "text"}}
- read_file: {"action": "read_file", "parameters": {"path": "file.txt"}}
- list_files: {"action": "list_files", "parameters": {"path": "."}}
- delete_file: {"action": "delete_file", "parameters": {"path": "file.txt"}}
- run_cmd: {"action": "run_cmd", "parameters": {"cmd": "command"}}
- run_python: {"action": "run_python", "parameters": {"code": "print('hello')"}}
- system_info: {"action": "system_info", "parameters": {}}
- registry_read: {"action": "registry_read", "parameters": {"key_path": "HKCU\\\\Environment"}}
- registry_write: {"action": "registry_write", "parameters": {"key_path": "...", "value_name": "...", "value_type": "REG_SZ", "value_data": "..."}}
- service_control: {"action": "service_control", "parameters": {"service_name": "Spooler", "action": "status"}}
- manage_users: {"action": "manage_users", "parameters": {"action": "list"}}
- network_config: {"action": "network_config", "parameters": {"action": "ipconfig"}}
- environment_variables: {"action": "environment_variables", "parameters": {"action": "get", "var_name": "PATH"}}
- system_power: {"action": "system_power", "parameters": {"action": "cancel"}}
- power_management: {"action": "power_management", "parameters": {"action": "status"}}
- scheduled_tasks: {"action": "scheduled_tasks", "parameters": {"action": "list"}}

Examples:
User: Create a file test.txt with hello
Assistant: {"action": "write_file", "parameters": {"path": "test.txt", "content": "hello"}}

User: What can you do?
Assistant: يمكنني مساعدتك في إنشاء الملفات، تشغيل الأوامر، عرض معلومات النظام، وغيرها.

IMPORTANT: Always use double backslashes in Windows paths: C:\\\\Users\\\\...
"""

RETRY_PROMPT = """Your previous response could not be parsed as a tool JSON object.
Return ONLY valid JSON in this exact shape:
{"action": "tool_name", "parameters": {"param": "value"}}
Do not include markdown, explanations, comments, or multiple actions."""

TECHNICAL_KEYWORDS = {
    "create", "write", "read", "list", "delete", "run", "execute", "command",
    "cmd", "python", "file", "folder", "system", "registry", "service",
    "network", "ipconfig", "dns", "user", "shutdown", "restart", "task",
    "environment", "power", "افتح", "اكتب", "انشئ", "انشي", "اقرأ", "اعرض",
    "شغل", "نفذ", "احذف", "ملف", "مجلد", "النظام", "امر", "أمر",
}


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract Jarvis tool JSON from model text. Returns dict or None."""
    if not text or not isinstance(text, str):
        return None

    for candidate in _json_candidates(text):
        data = _loads_relaxed(candidate)
        parsed = _normalize_tool_json(data)
        if parsed:
            return parsed

    return None


def ask_llm(prompt: str, model_choice: str = "groq") -> Tuple[str, str, Optional[Dict[str, Any]]]:
    """Return (raw_text, provider_name, parsed_data_or_None)."""
    provider_name = _normalize_model_choice(model_choice)
    retry_on_parse_failure = _looks_like_technical_request(prompt)
    last_raw = ""
    last_provider = provider_name

    for attempt in range(2):
        retry_note = RETRY_PROMPT if attempt == 1 else None
        raw, provider = _call_provider(prompt, provider_name, retry_note=retry_note)
        last_raw, last_provider = raw, provider

        if provider == "error":
            return raw, provider, None

        parsed = extract_json(raw)
        if parsed:
            return raw, provider, parsed

        if not retry_on_parse_failure and "{" not in raw:
            break

    return last_raw, last_provider, None


def _call_provider(prompt: str, model_choice: str, retry_note: str = None) -> Tuple[str, str]:
    if model_choice == "groq":
        return _ask_groq(prompt, retry_note=retry_note)
    if model_choice in LOCAL_MODELS:
        return _ask_ollama(prompt, model_choice, retry_note=retry_note)
    return f"Unknown model: {model_choice}", "error"


def _ask_groq(prompt: str, retry_note: str = None) -> Tuple[str, str]:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return "Error: GROQ_API_KEY is not configured", "error"

    payload = {
        "model": GROQ_MODEL,
        "messages": _build_messages(prompt, retry_note=retry_note),
        "temperature": 0.2,
        "max_tokens": 2048,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"], "groq"
    except Exception as exc:
        return f"Error: {str(exc)[:200]}", "error"


def _ask_ollama(prompt: str, model: str, retry_note: str = None) -> Tuple[str, str]:
    payload = {
        "model": model,
        "messages": _build_messages(prompt, retry_note=retry_note),
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["message"]["content"], model
    except Exception as exc:
        return f"Error: {str(exc)[:200]}", "error"


def _build_messages(prompt: str, retry_note: str = None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if retry_note:
        messages.append({"role": "system", "content": retry_note})
    messages.append({"role": "user", "content": prompt})
    return messages


def _normalize_model_choice(model_choice: str) -> str:
    if model_choice == "local":
        return DEFAULT_LOCAL_MODEL
    return model_choice or "groq"


def _normalize_tool_json(data: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(data, dict):
        return None

    if "action" in data:
        action = data.get("action")
        has_parameters = "parameters" in data
        parameters = data.get("parameters", {})
        if not isinstance(action, str) or not action:
            return None
        if not isinstance(parameters, dict):
            parameters = {}
        if not has_parameters:
            parameters = {key: value for key, value in data.items() if key != "action"}
        return {"action": action, "parameters": parameters}

    if "actions" in data and isinstance(data["actions"], list) and data["actions"]:
        first = data["actions"][0]
        if not isinstance(first, dict):
            return None
        action = first.get("action") or first.get("tool")
        if not isinstance(action, str) or not action:
            return None
        parameters = first.get("parameters")
        if not isinstance(parameters, dict):
            parameters = {
                key: value
                for key, value in first.items()
                if key not in {"action", "tool"}
            }
        return {"action": action, "parameters": parameters}

    return None


def _json_candidates(text: str):
    cleaned = _strip_code_fences(text)
    direct = cleaned.strip()
    if direct:
        yield direct

    for match in re.finditer(r"\{", cleaned):
        candidate = _balanced_object_from(cleaned, match.start())
        if candidate:
            yield candidate


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _balanced_object_from(text: str, start: int) -> Optional[str]:
    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    return None


def _loads_relaxed(candidate: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    repaired = candidate.strip()
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    repaired = re.sub(r"(?<!\\)'", '"', repaired)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        return None


def _looks_like_technical_request(prompt: str) -> bool:
    lowered = (prompt or "").lower()
    return any(keyword in lowered for keyword in TECHNICAL_KEYWORDS)
