# -*- coding: utf-8 -*-
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import tools.file_tools
import tools.cmd_tools
import tools.registry_tools
import tools.service_tools
import tools.user_tools
import tools.system_tools
import tools.network_tools
import tools.env_tools
import tools.power_tools

from schemas.tool_schema import ToolRequest
from core.executor import Executor
from tools.registry import list_tools, requires_confirmation
from providers.llm_provider import ask_llm, LOCAL_MODELS

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
* { font-family: 'Cairo', sans-serif !important; }
.stApp { background: #212121 !important; }
.main .block-container { padding: 2rem 3rem !important; max-width: 900px !important; margin: 0 auto !important; }
.chat-header { text-align: center; padding: 1.5rem; border-bottom: 1px solid #333; margin-bottom: 2rem; }
.chat-header h1 { color: #fff !important; font-size: 1.8rem !important; margin: 0 !important; }
.stChatMessage { background: transparent !important; border: none !important; padding: 1rem 0 !important; }
.assistant-bubble { background: #2f2f2f !important; border-radius: 1rem !important; padding: 1.2rem !important; margin: 0.5rem 0 !important; color: #fff !important; line-height: 1.6 !important; }
.tool-execution { background: #1a1a1a !important; border-left: 3px solid #667eea !important; padding: 1rem !important; border-radius: 0.5rem !important; margin: 1rem 0 !important; font-family: 'Consolas', monospace !important; }
.tool-success { border-left-color: #4caf50 !important; }
.tool-error { border-left-color: #f44336 !important; }
.stChatInput { background: #2f2f2f !important; border-radius: 1.5rem !important; padding: 0.5rem 1rem !important; border: 1px solid #444 !important; }
.stChatInput input { background: transparent !important; color: #fff !important; border: none !important; }
[data-testid="stSidebar"] { background: #171717 !important; border-right: 1px solid #333 !important; }
[data-testid="stSidebar"] .stMarkdown { color: #fff !important; }
.stButton button { background: #2f2f2f !important; color: #fff !important; border: 1px solid #444 !important; border-radius: 0.5rem !important; }
.stButton button:hover { background: #3f3f3f !important; border-color: #667eea !important; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #212121; }
::-webkit-scrollbar-thumb { background: #444; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🤖 Jarvis AI")
    st.markdown("---")
    st.markdown("#### 🎯 Model")
    model_options = ["groq"] + list(LOCAL_MODELS.keys())
    model_labels = {"groq": "☁️ Groq (Fast)"}
    model_labels.update(LOCAL_MODELS)
    model_choice = st.selectbox("Choose model", model_options, format_func=lambda x: model_labels.get(x, x), index=0)
    st.markdown("---")
    tools_count = len(list_tools())
    st.metric("Registered Tools", tools_count)
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.markdown('<div class="chat-header"><h1>🤖 Jarvis AI</h1></div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f'<div class="assistant-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

if len(st.session_state.messages) == 0:
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem;">
        <h1 style="color: #fff !important; font-size: 2.5rem !important;">Welcome to Jarvis AI</h1>
        <p style="color: #aaa !important; font-size: 1.1rem !important;">Your smart Windows automation assistant</p>
        <p style="color: #888 !important; margin-top: 2rem;">💡 Try: "Create test.txt with hello" or "Hello" or "System info"</p>
    </div>
    """, unsafe_allow_html=True)

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response_text, provider, parsed_data = ask_llm(prompt, model_choice)
                
                if parsed_data and parsed_data.get("action") and parsed_data.get("action") != "none":
                    action = parsed_data["action"]
                    params = parsed_data.get("parameters", {})
                    
                    if requires_confirmation(action):
                        warning_msg = f"⚠️ Tool **{action}** is dangerous. Do you want to proceed?"
                        st.markdown(f'<div class="assistant-bubble">{warning_msg}</div>', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Yes, execute", key="confirm_yes"):
                                try:
                                    request = ToolRequest(action=action, parameters=params)
                                    executor = Executor()
                                    result = executor.execute(request)
                                    if result.success:
                                        result_html = f'<div class="tool-execution tool-success">✅ {action}: {result.data}</div>'
                                    else:
                                        result_html = f'<div class="tool-execution tool-error">❌ {action}: {result.error}</div>'
                                    st.markdown(result_html, unsafe_allow_html=True)
                                    st.session_state.messages.append({"role": "assistant", "content": result_html})
                                except Exception as e:
                                    error_html = f'<div class="tool-execution tool-error">❌ Error: {str(e)}</div>'
                                    st.markdown(error_html, unsafe_allow_html=True)
                                    st.session_state.messages.append({"role": "assistant", "content": error_html})
                                st.rerun()
                        with col2:
                            if st.button(" Cancel", key="confirm_no"):
                                cancel_msg = "Operation canceled."
                                st.markdown(f'<div class="assistant-bubble">{cancel_msg}</div>', unsafe_allow_html=True)
                                st.session_state.messages.append({"role": "assistant", "content": cancel_msg})
                                st.rerun()
                        st.stop()
                    else:
                        try:
                            request = ToolRequest(action=action, parameters=params)
                            executor = Executor()
                            result = executor.execute(request)
                            if result.success:
                                result_html = f'<div class="tool-execution tool-success">✅ {action}: {result.data}</div>'
                            else:
                                result_html = f'<div class="tool-execution tool-error">❌ {action}: {result.error}</div>'
                            st.markdown(result_html, unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": result_html})
                        except Exception as e:
                            error_html = f'<div class="tool-execution tool-error">❌ Error: {str(e)}</div>'
                            st.markdown(error_html, unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": error_html})
                else:
                    st.markdown(f'<div class="assistant-bubble">{response_text}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.markdown(f'<div class="assistant-bubble">{error_msg}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    st.rerun()
