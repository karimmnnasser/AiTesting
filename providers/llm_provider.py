# -*- coding: utf-8 -*-
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path("D:/JarvisAI/.env"))

OLLAMA_URL = "http://localhost:11434/api/chat"

LOCAL_MODELS = {
    "qwen3:8b": "Qwen3 8B",
    "deepseek-coder-v2:16b": "DeepSeek Coder 16B",
    "qwen2.5:7b-instruct": "Qwen2.5 Instruct",
    "llama3.1:8b": "Llama 3.1 8B",
    "qwen2.5-coder:7b": "Qwen Coder 7B",
    "qwen2.5vl:7b": "Qwen2.5 VL 7B",
}

SYSTEM_PROMPT = """You are Jarvis AI, a Windows automation assistant.

RULES:
1. If the user asks you to DO something technical (create file, run command, etc.), respond ONLY with valid JSON:
{"action": "tool_name", "parameters": {"param": "value"}}

2. If the user asks a general question or greets you, respond naturally in Arabic WITHOUT JSON.

Available tools:
- write_file: {"action": "write_file", "parameters": {"path": "...", "content": "..."}}
- read_file: {"action": "read_file", "parameters": {"path": "..."}}
- list_files: {"action": "list_files", "parameters": {"path": "..."}}
- run_cmd: {"action": "run_cmd", "parameters": {"cmd": "..."}}
- system_info: {"action": "system_info", "parameters": {}}

Examples:
- User: "Create a file test.txt with hello" -> {"action": "write_file", "parameters": {"path": "test.txt", "content": "hello"}}
- User: "Hello" -> مرحباً! كيف يمكنني مساعدتك؟
- User: "What is Python?" -> Python هي لغة برمجة...

Respond in Arabic always."""


def extract_json(text: str):
    """Extract JSON from text. Returns dict or None."""
    if not text:
        return None
    
    cleaned = text.replace("`json", "").replace("`", "").strip()
    
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        try:
            data = json.loads(cleaned[start:end])
            if "action" in data:
                action = data["action"]
                params = data.get("parameters", {})
                if not params:
                    params = {k: v for k, v in data.items() if k != "action"}
                return {"action": action, "parameters": params}
            if "actions" in data and isinstance(data["actions"], list) and len(data["actions"]) > 0:
                first = data["actions"][0]
                return {"action": first.get("action", "none"), "parameters": {k: v for k, v in first.items() if k != "action"}}
        except:
            pass
    
    return None


def ask_llm(prompt: str, model_choice: str = "groq"):
    """Returns: (raw_text, provider_name, parsed_data_or_None)"""
    
    # Cloud providers
    if model_choice == "groq":
        api_key = os.environ.get("GROQ_API_KEY", "")
        if api_key:
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
                r.raise_for_status()
                raw = r.json()["choices"][0]["message"]["content"]
                return raw, "groq", extract_json(raw)
            except Exception as e:
                return f"Error: {str(e)[:100]}", "error", None
    
    # Local Ollama models
    if model_choice in LOCAL_MODELS:
        try:
            payload = {
                "model": model_choice,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.7, "num_ctx": 4096}
            }
            r = requests.post(OLLAMA_URL, json=payload, timeout=120)
            r.raise_for_status()
            raw = r.json()["message"]["content"]
            return raw, model_choice, extract_json(raw)
        except Exception as e:
            return f"Error: {str(e)[:100]}", "error", None
    
    return "Unknown model", "error", None
