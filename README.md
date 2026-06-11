# Jarvis AI - Windows Automation Agent

Local AI automation agent for Windows with Ollama + Groq fallback.

## Features

- Hybrid AI: Ollama (local) + Groq (cloud)
- 18+ built-in tools (files, browser, Git, email, images)
- JSON Repair + Verification + Auto-Retry
- SQLite + FTS5 smart memory
- Gradio web UI at http://localhost:7860

## Quick Start

    git clone https://github.com/YOUR_USERNAME/jarvis-ai.git
    cd jarvis-ai
    python -m venv JarvisEnv
    JarvisEnv\Scripts\activate
    pip install -r requirements.txt
    playwright install chromium
    copy .env.example .env
    python jarvis_v4.py

## Tools

- Files: write, read, list, delete, organize
- Commands: run_cmd, run_python, system_info
- Browser: open, screenshot
- Productivity: clipboard, notify, email, images
- Git: status, add, commit, push
- Users: list, create

## Security

- .env never committed
- Dangerous commands blocked
- Paths isolated to Desktop

## License

MIT
