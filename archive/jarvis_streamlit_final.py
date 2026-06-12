# -*- coding: utf-8 -*-
"""
Jarvis AI - الواجهة النهائية
تربط كل المكونات: LLM + Executor + Tools + Memory
"""
import streamlit as st
import sys
from pathlib import Path

# إضافة المسار الحالي لـ Python path
sys.path.insert(0, str(Path(__file__).parent))

# استيراد الأدوات (تسجيلها تلقائياً)
import tools.file_tools
import tools.cmd_tools
import tools.registry_tools
import tools.service_tools
import tools.user_tools
import tools.system_tools
import tools.network_tools
import tools.env_tools
import tools.power_tools
import tools.scheduled_tools

from schemas.tool_schema import ToolRequest, ToolResponse, LLMResponse
from core.executor import Executor
from tools.registry import list_tools, requires_confirmation
from providers.llm_provider import ask_llm
from database.memory import Memory
from utils.json_parser import extract_json

# تهيئة الذاكرة
memory = Memory()

# ============================================================
# إعدادات الصفحة
# ============================================================
st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="wide")

# ============================================================
# CSS مخصص
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important; }
    .jarvis-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        padding: 30px !important; border-radius: 20px !important;
        margin-bottom: 20px !important; text-align: center !important;
        color: white !important; box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3) !important;
    }
    .jarvis-header h1 { color: white !important; font-size: 3em !important; margin: 0 !important; }
    .jarvis-header p { color: rgba(255,255,255,0.9) !important; font-size: 1.2em !important; margin-top: 10px !important; }
    .stChatMessage { background: rgba(255,255,255,0.05) !important; border-radius: 15px !important; margin: 10px 0 !important; }
    .stTextInput input, .stTextArea textarea { background: rgba(255,255,255,0.1) !important; border: none !important; color: white !important; border-radius: 10px !important; }
    .confirmation-box {
        background: rgba(255, 165, 0, 0.2) !important;
        border: 2px solid orange !important;
        padding: 20px !important;
        border-radius: 15px !important;
        margin: 15px 0 !important;
    }
    .success-box {
        background: rgba(0, 255, 0, 0.1) !important;
        border: 1px solid green !important;
        padding: 15px !important;
        border-radius: 10px !important;
    }
    .error-box {
        background: rgba(255, 0, 0, 0.1) !important;
        border: 1px solid red !important;
        padding: 15px !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Header
# ============================================================
st.markdown('<div class="jarvis-header"><h1>🤖 Jarvis AI</h1><p>مساعدك الذكي الشامل لأتمتة Windows</p></div>', unsafe_allow_html=True)

# ============================================================
# الشريط الجانبي
# ============================================================
with st.sidebar:
    st.markdown("### 📊 النظام")
    
    # عدد الأدوات المسجلة
    tools_list = list_tools()
    st.metric("الأدوات المسجلة", len(tools_list))
    
    # اختيار النموذج
    st.markdown("---")
    st.markdown("### 🎯 النموذج")
    provider_choice = st.selectbox(
        "اختر النموذج المفضل",
        ["local", "groq"],
        format_func=lambda x: "🖥️ محلي (Ollama)" if x == "local" else "☁️ Groq (سحابي)",
        index=1  # Groq افتراضي
    )
    
    # زر مسح المحادثة
    st.markdown("---")
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages = []
        if "pending_confirmation" in st.session_state:
            del st.session_state.pending_confirmation
        st.rerun()
    
    # آخر المهام
    st.markdown("---")
    st.markdown("### 📜 آخر المهام")
    try:
        recent = memory.get_recent(5)
        if recent:
            for r in recent:
                status_icon = "✅" if r[4] == 1 else "❌"
                st.caption(f"{status_icon} **[{r[1]}]** {r[0][:40]}...")
        else:
            st.info("لا توجد مهام سابقة")
    except Exception as e:
        st.error(f"خطأ في تحميل السجل: {e}")

# ============================================================
# إدارة حالة التأكيد
# ============================================================
if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "👋 مرحباً! أنا Jarvis. كيف يمكنني مساعدتك؟"}]

# ============================================================
# عرض الرسائل
# ============================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ============================================================
# عرض طلب التأكيد إذا كان موجوداً
# ============================================================
if st.session_state.pending_confirmation:
    pending = st.session_state.pending_confirmation
    action = pending["action"]
    params = pending["parameters"]
    
    st.markdown("---")
    st.markdown("### ⚠️ تأكيد مطلوب")
    st.warning(f"الأداة **{action}** خطيرة وتتطلب تأكيدك قبل التنفيذ.")
    
    with st.container():
        st.markdown("**المعاملات:**")
        for key, value in params.items():
            st.code(f"{key}: {value}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ تنفيذ", type="primary", use_container_width=True, key="confirm_execute"):
                # تنفيذ الأمر
                try:
                    request = ToolRequest(action=action, parameters=params)
                    executor = Executor()
                    result = executor.execute(request)
                    
                    # عرض النتيجة
                    response_msg = f"**[{action}]**\n\n"
                    if result.success:
                        response_msg += f"✅ {result.data}"
                    else:
                        response_msg += f"❌ {result.error}"
                    
                    st.session_state.messages.append({"role": "assistant", "content": response_msg})
                    
                    # حفظ في الذاكرة
                    memory.save(
                        pending["original_prompt"],
                        action,
                        result.data if result.success else result.error,
                        pending["provider"],
                        1 if result.success else 0
                    )
                    
                    # مسح التأكيد
                    del st.session_state.pending_confirmation
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"خطأ في التنفيذ: {e}")
                    del st.session_state.pending_confirmation
        
        with col2:
            if st.button("❌ إلغاء", use_container_width=True, key="confirm_cancel"):
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ تم إلغاء تنفيذ **{action}**"
                })
                del st.session_state.pending_confirmation
                st.rerun()

# ============================================================
# إدخال المستخدم
# ============================================================
if prompt := st.chat_input("اكتب مهمتك هنا..."):
    # إضافة رسالة المستخدم
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # معالجة الأمر
    with st.chat_message("assistant"):
        with st.spinner("⏳ جاري التفكير..."):
            try:
                # استدعاء LLM
                raw_response, provider, parsed_data = ask_llm(prompt, provider_choice)
                
                # استخراج action و parameters
                action = parsed_data.get("action", "none")
                params = parsed_data.get("parameters", {})
                
                # إذا لم يفهم النموذج
                if action == "none" or not action:
                    error_msg = "❌ لم يستطع النموذج فهم الأمر. حاول صياغته بشكل أوضح."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    memory.save(prompt, "error", raw_response[:200], provider, 0)
                else:
                    # التحقق من إذا كانت الأداة خطيرة
                    if requires_confirmation(action):
                        # حفظ طلب التأكيد
                        st.session_state.pending_confirmation = {
                            "action": action,
                            "parameters": params,
                            "provider": provider,
                            "original_prompt": prompt
                        }
                        
                        confirmation_msg = f"⚠️ الأداة **{action}** خطيرة وتتطلب تأكيدك. انظر الأعلى."
                        st.warning(confirmation_msg)
                        st.session_state.messages.append({"role": "assistant", "content": confirmation_msg})
                    else:
                        # تنفيذ مباشر
                        try:
                            request = ToolRequest(action=action, parameters=params)
                            executor = Executor()
                            result = executor.execute(request)
                            
                            # عرض النتيجة
                            response_msg = f"**[{action}]**\n\n"
                            if result.success:
                                response_msg += f"✅ {result.data}"
                            else:
                                response_msg += f"❌ {result.error}"
                            
                            st.markdown(response_msg)
                            st.session_state.messages.append({"role": "assistant", "content": response_msg})
                            
                            # حفظ في الذاكرة
                            memory.save(
                                prompt,
                                action,
                                result.data if result.success else result.error,
                                provider,
                                1 if result.success else 0
                            )
                            
                        except Exception as e:
                            error_msg = f"❌ خطأ في تنفيذ الأداة: {e}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                            memory.save(prompt, action, str(e), provider, 0)
                
            except Exception as e:
                error_msg = f"❌ خطأ غير متوقع: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ============================================================
# التبويبات
# ============================================================
tab1, tab2, tab3 = st.tabs(["📜 السجل", "📁 المشاريع", "🔍 التدقيق"])

with tab1:
    st.markdown("### 📜 آخر 20 مهمة")
    if st.button("🔄 تحديث السجل"):
        st.rerun()
    
    try:
        recent = memory.get_recent(20)
        if recent:
            for r in recent:
                status = "✅" if r[4] == 1 else "❌"
                with st.expander(f"{status} **[{r[1]}]** - {r[0][:80]}"):
                    st.code(r[2] if r[2] else "لا توجد نتائج")
        else:
            st.info("لا توجد مهام سابقة")
    except Exception as e:
        st.error(f"خطأ في تحميل السجل: {e}")

with tab2:
    st.markdown("### 📁 المشاريع المحفوظة")
    try:
        projects = memory.get_projects()
        if projects:
            for p in projects:
                st.markdown(f"#### 📁 {p[0]}")
                st.markdown(p[1])
                st.markdown("---")
        else:
            st.info("لا توجد مشاريع محفوظة")
    except Exception as e:
        st.error(f"خطأ في تحميل المشاريع: {e}")

with tab3:
    st.markdown("### 🔍 سجل التدقيق (آخر 50 عملية)")
    try:
        logs = memory.get_audit_log(50)
        if logs:
            for log in logs:
                ts, act, res, stat, err = log
                status_icon = "✅" if stat == 'success' else "❌"
                st.caption(f"{status_icon} **{act}** - {res} ({ts[:19]})")
                if err:
                    st.warning(f"خطأ: {err}")
        else:
            st.info("لا توجد سجلات تدقيق")
    except Exception as e:
        st.error(f"خطأ في تحميل سجل التدقيق: {e}")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.9em;'>"
    "🤖 Jarvis AI Pro - مبني بـ Streamlit + Tool Registry + Multi-Provider LLM"
    "</div>",
    unsafe_allow_html=True
)
