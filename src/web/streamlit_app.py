"""Streamlit web interface for the AI Grant Engine."""

import asyncio
import os
import sys
import threading
import streamlit as st
from pathlib import Path

# Fix import paths for Streamlit Cloud deployment
# The app runs from /mount/src/ai-grant-engine/ so we need to add the root to sys.path
_ROOT = Path(__file__).parent.parent.parent  # ai-grant-engine/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Load environment variables from secrets (for cloud deployment)
def _load_secrets_to_env():
    """Load Streamlit secrets into env vars for the settings module."""
    secret_keys = [
        "GROQ_API_KEY", "GEMINI_API_KEY", "TOGETHER_API_KEY",
        "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "MISTRAL_API_KEY",
    ]
    for key in secret_keys:
        val = os.environ.get(key, "")
        if not val:
            try:
                val = st.secrets.get(key, "")
            except Exception:
                pass
        if val:
            os.environ[key] = val

_load_secrets_to_env()

st.set_page_config(
    page_title="AI Grant Engine - מנוע מענקים",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* ===== ANIMATED BACKGROUND ===== */
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes float {
    0%   { transform: translateY(0px) rotate(0deg); opacity: 0.15; }
    50%  { transform: translateY(-30px) rotate(180deg); opacity: 0.25; }
    100% { transform: translateY(0px) rotate(360deg); opacity: 0.15; }
}

@keyframes pulse-glow {
    0%   { box-shadow: 0 0 5px rgba(99,102,241,0.3), 0 0 20px rgba(99,102,241,0.1); }
    50%  { box-shadow: 0 0 20px rgba(99,102,241,0.6), 0 0 60px rgba(99,102,241,0.2); }
    100% { box-shadow: 0 0 5px rgba(99,102,241,0.3), 0 0 20px rgba(99,102,241,0.1); }
}

@keyframes fadeSlideDown {
    from { opacity: 0; transform: translateY(-30px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position: 200% center; }
}

@keyframes orbit {
    from { transform: rotate(0deg) translateX(120px) rotate(0deg); }
    to   { transform: rotate(360deg) translateX(120px) rotate(-360deg); }
}

@keyframes particle-float {
    0%   { transform: translate(0, 0) scale(1); opacity: 0.6; }
    33%  { transform: translate(30px, -50px) scale(1.2); opacity: 0.8; }
    66%  { transform: translate(-20px, -80px) scale(0.9); opacity: 0.5; }
    100% { transform: translate(0, -120px) scale(0.5); opacity: 0; }
}

/* Main app background */
.stApp {
    background: linear-gradient(-45deg, #0f0c29, #302b63, #1a1a4e, #0d1b4b, #1e0a3c);
    background-size: 400% 400%;
    animation: gradientShift 12s ease infinite;
    min-height: 100vh;
}

/* Floating orbs in background */
.stApp::before {
    content: '';
    position: fixed;
    top: 10%;
    left: 5%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
    border-radius: 50%;
    animation: float 8s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
}

.stApp::after {
    content: '';
    position: fixed;
    bottom: 10%;
    right: 5%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%);
    border-radius: 50%;
    animation: float 11s ease-in-out infinite reverse;
    pointer-events: none;
    z-index: 0;
}

/* ===== HEADER HERO ===== */
.hero-container {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    animation: fadeSlideDown 0.8s ease-out;
    position: relative;
}

.hero-title {
    font-size: 3rem;
    font-weight: 900;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399, #a78bfa);
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 4s linear infinite;
    letter-spacing: -1px;
    margin-bottom: 0.5rem;
    direction: rtl;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: rgba(200, 210, 255, 0.75);
    direction: rtl;
    margin-bottom: 0.5rem;
    animation: fadeSlideDown 1s ease-out 0.2s both;
}

.hero-badge {
    display: inline-block;
    background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.25));
    border: 1px solid rgba(139,92,246,0.4);
    color: #c4b5fd;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    margin: 0.3rem 0.25rem;
    animation: fadeSlideUp 1s ease-out 0.4s both;
    backdrop-filter: blur(8px);
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(15,12,41,0.97) 0%, rgba(30,10,60,0.97) 100%);
    border-right: 1px solid rgba(139,92,246,0.25);
    backdrop-filter: blur(16px);
}

section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #c4b5fd !important;
}

/* ===== CARDS / CONTAINERS ===== */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
div.stForm {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px) !important;
    transition: border-color 0.3s, transform 0.2s;
}

div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(139,92,246,0.5) !important;
    transform: translateY(-2px);
}

/* ===== INPUTS ===== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(139,92,246,0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    transition: border-color 0.3s, box-shadow 0.3s !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(139,92,246,0.7) !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.15) !important;
}

/* ===== PRIMARY BUTTON ===== */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7) !important;
    background-size: 200% auto !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.3s ease !important;
    animation: pulse-glow 2.5s ease-in-out infinite;
    letter-spacing: 0.5px;
}

.stButton > button[kind="primary"]:hover {
    background-position: right center !important;
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 8px 30px rgba(99,102,241,0.5) !important;
}

.stButton > button[kind="primary"]:active {
    transform: translateY(-1px) scale(0.99) !important;
}

/* Secondary buttons */
.stButton > button:not([kind="primary"]) {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(139,92,246,0.35) !important;
    border-radius: 10px !important;
    color: #c4b5fd !important;
    transition: all 0.2s !important;
}

.stButton > button:not([kind="primary"]):hover {
    background: rgba(139,92,246,0.15) !important;
    border-color: rgba(139,92,246,0.6) !important;
    transform: translateY(-1px) !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: rgba(196,181,253,0.7) !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.35), rgba(139,92,246,0.35)) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(139,92,246,0.4) !important;
}

/* ===== METRICS ===== */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 14px !important;
    padding: 1rem !important;
    animation: fadeSlideUp 0.6s ease-out both;
    transition: transform 0.2s, box-shadow 0.2s;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(99,102,241,0.2);
}

div[data-testid="stMetricValue"] {
    color: #a78bfa !important;
    font-weight: 800 !important;
}

/* ===== ALERTS ===== */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
    border-left-width: 4px !important;
}

/* ===== PROGRESS BAR ===== */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7) !important;
    background-size: 200% auto !important;
    animation: shimmer 2s linear infinite !important;
    border-radius: 4px !important;
}

/* ===== EXPANDER ===== */
details {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
    margin: 0.5rem 0 !important;
    transition: border-color 0.3s !important;
}

details:hover {
    border-color: rgba(139,92,246,0.45) !important;
}

details summary {
    color: #c4b5fd !important;
    font-weight: 600 !important;
    cursor: pointer !important;
}

/* ===== FILE UPLOADER ===== */
div[data-testid="stFileUploader"] {
    border: 2px dashed rgba(139,92,246,0.35) !important;
    border-radius: 14px !important;
    background: rgba(99,102,241,0.04) !important;
    transition: border-color 0.3s, background 0.3s !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: rgba(139,92,246,0.65) !important;
    background: rgba(99,102,241,0.08) !important;
}

/* ===== DOWNLOAD BUTTON ===== */
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(52,211,153,0.2)) !important;
    border: 1px solid rgba(52,211,153,0.4) !important;
    color: #6ee7b7 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}

div[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, rgba(16,185,129,0.35), rgba(52,211,153,0.35)) !important;
    border-color: rgba(52,211,153,0.7) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(52,211,153,0.2) !important;
}

/* ===== SPINNER ===== */
.stSpinner > div {
    border-top-color: #8b5cf6 !important;
}

/* ===== CHECKBOX ===== */
.stCheckbox label {
    color: #c4b5fd !important;
}

/* ===== ALL TEXT ===== */
.stMarkdown p, .stMarkdown li { color: #cbd5e1 !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #e2e8f0 !important; }
label { color: #94a3b8 !important; }

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #6366f1, #8b5cf6);
    border-radius: 3px;
}

/* ===== STAGE PROGRESS ITEMS ===== */
.stage-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 1rem;
    border-radius: 10px;
    margin: 0.3rem 0;
    transition: all 0.3s;
    direction: rtl;
}

.stage-active {
    background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
    border: 1px solid rgba(139,92,246,0.4);
    animation: pulse-glow 2s ease-in-out infinite;
}

.stage-done {
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(52,211,153,0.25);
    color: #6ee7b7;
}

.stage-pending {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    color: rgba(148,163,184,0.5);
}
</style>
"""


def main():
    # Inject CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Hero header
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🏛️ מנוע המענקים</div>
            <div style="font-size:1.4rem; color:#a78bfa; font-weight:600; margin-bottom:0.4rem;">
                AI Grant Engine
            </div>
            <div class="hero-subtitle">
                מערכת אוטומטית לכתיבת בקשות מענק · מסלול תנופה · רשות החדשנות הישראלית
            </div>
            <div>
                <span class="hero-badge">🤖 7 מודלי AI</span>
                <span class="hero-badge">📄 21 סעיפי בקשה</span>
                <span class="hero-badge">💰 עד 200,000 ₪ מענק</span>
                <span class="hero-badge">⚡ Zero Human Touch</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar - Configuration
    with st.sidebar:
        st.markdown(
            """<div style='text-align:center; padding: 0.5rem 0 1rem;'>
            <div style='font-size:2rem;'>🏛️</div>
            <div style='color:#a78bfa; font-weight:700; font-size:1.05rem;'>Grant Engine</div>
            <div style='color:rgba(148,163,184,0.6); font-size:0.75rem;'>v2.0 · מסלול תנופה</div>
            </div>
            <hr style='border-color:rgba(139,92,246,0.2); margin-bottom:1rem;'>""",
            unsafe_allow_html=True,
        )
        st.markdown("### ⚙️ הגדרות מודל AI")
        _render_provider_config()

    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📝 קלט", "🔄 תהליך", "📄 תוצרים", "📊 הערכה"])

    with tab1:
        _render_input_form()

    with tab2:
        _render_pipeline_progress()

    with tab3:
        _render_outputs()

    with tab4:
        _render_evaluation()


def _render_provider_config():
    """Render LLM provider configuration in sidebar."""
    st.subheader("🤖 ספקי LLM")
    st.caption("הזן מפתח API לפחות אחד")

    providers = {
        "Groq (חינם)": "groq_api_key",
        "Google Gemini (חינם)": "gemini_api_key",
        "Together AI (חינם)": "together_api_key",
        "OpenRouter": "openrouter_api_key",
        "Claude (Anthropic)": "anthropic_api_key",
        "OpenAI (GPT-4)": "openai_api_key",
        "Mistral": "mistral_api_key",
    }

    for label, key in providers.items():
        st.text_input(label, type="password", key=key)

    configured = sum(1 for k in providers.values() if st.session_state.get(k))
    if configured > 0:
        st.success(f"✓ {configured} ספקים מוגדרים")
    else:
        st.warning("⚠️ יש להגדיר לפחות ספק אחד")


def _render_input_form():
    """Render the startup input form."""
    st.markdown("<div style='direction: rtl; text-align: right;'>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        startup_name = st.text_input("שם המיזם *", key="startup_name")
        entity_type = st.selectbox(
            "סוג מגיש",
            options=["private_entrepreneur", "new_company"],
            format_func=lambda x: "יזם פרטי" if x == "private_entrepreneur" else "חברה חדשה",
            key="entity_type",
        )
        is_woman = st.checkbox("יזמת (בונוס 10% למענק)", key="is_woman")

    with col2:
        github_url = st.text_input("קישור GitHub (אופציונלי)", key="github_url")
        linkedin_url = st.text_input("קישור LinkedIn (אופציונלי)", key="linkedin_url")

    startup_desc = st.text_area(
        "תיאור המיזם *",
        height=200,
        placeholder="תאר את המיזם, הטכנולוגיה, הבעיה שאתה פותר והפתרון המוצע...",
        key="startup_desc",
    )

    # File uploads
    st.subheader("📎 העלאת קבצים")
    uploaded_files = st.file_uploader(
        "העלה מצגת, קורות חיים, מסמכי אפיון (PDF, PPTX, DOCX)",
        accept_multiple_files=True,
        type=["pdf", "pptx", "docx", "txt"],
        key="uploads",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Submit button
    if st.button("🚀 התחל תהליך כתיבת בקשה", type="primary", use_container_width=True):
        if not startup_name or not startup_desc:
            st.error("יש למלא שם מיזם ותיאור")
            return

        # Save uploaded files
        saved_files = []
        if uploaded_files:
            upload_dir = Path("./uploads")
            upload_dir.mkdir(exist_ok=True)
            for f in uploaded_files:
                file_path = upload_dir / f.name
                file_path.write_bytes(f.read())
                saved_files.append(str(file_path))

        # Store state
        st.session_state["pipeline_input"] = {
            "startup_name": startup_name,
            "startup_description": startup_desc,
            "github_urls": [github_url] if github_url else [],
            "linkedin_urls": [linkedin_url] if linkedin_url else [],
            "uploaded_files": saved_files,
            "is_woman_entrepreneur": is_woman,
            "entity_type": entity_type,
        }
        st.session_state["pipeline_running"] = True
        st.rerun()


def _render_pipeline_progress():
    """Render pipeline execution progress."""
    if not st.session_state.get("pipeline_running"):
        st.info("👈 מלא את הטופס בלשונית 'קלט' כדי להתחיל")
        return

    if st.session_state.get("pipeline_complete"):
        st.success("✅ התהליך הושלם בהצלחה!")
        _display_results_summary()
        return

    st.markdown(
        "<h2 style='text-align:center; color:#a78bfa; direction:rtl;'>🔄 מנוע המענקים בפעולה...</h2>",
        unsafe_allow_html=True,
    )

    stages = [
        ("ingestion",         "📥", "קליטת מידע",       "סריקת GitHub, מצגות ומסמכים"),
        ("matching",          "✅", "בדיקת התאמה",       "אימות עמידה בתנאי סף"),
        ("drafting_strategy", "📊", "אסטרטגיה",         "כתיבת נרטיב עסקי ושיווקי"),
        ("drafting_technical","🔬", "כתיבה טכנית",       "ניסוח פרקי מו\"פ וחדשנות"),
        ("financials",        "💰", "תקציב",             "בניית תקציב אופטימלי"),
        ("evaluation",        "🎯", "הערכה",             "בדיקת איכות (Red Team)"),
        ("output",            "📄", "הפקת מסמכים",       "יצירת Word ו-Excel"),
    ]

    current = st.session_state.get("current_stage", "ingestion")
    stage_ids = [s[0] for s in stages]
    current_idx = stage_ids.index(current) if current in stage_ids else 0

    stages_html = ""
    for i, (stage_id, icon, label, desc) in enumerate(stages):
        if i < current_idx:
            cls = "stage-done"
            status_icon = "✔"
        elif i == current_idx:
            cls = "stage-active"
            status_icon = "⏳"
        else:
            cls = "stage-pending"
            status_icon = "○"
        stages_html += f"""
        <div class="stage-item {cls}">
            <span style="font-size:1.3rem">{icon}</span>
            <div style="flex:1">
                <div style="font-weight:700; font-size:0.95rem">{label}</div>
                <div style="font-size:0.78rem; opacity:0.7">{desc}</div>
            </div>
            <span style="font-size:1.1rem">{status_icon}</span>
        </div>"""

    st.markdown(f"<div style='max-width:600px; margin:0 auto'>{stages_html}</div>", unsafe_allow_html=True)
    st.markdown("")

    # Run pipeline
    if st.session_state.get("pipeline_input") and not st.session_state.get("pipeline_result"):
        with st.spinner("🤖 המערכת כותבת את הבקשה... (עלול לקחת 2-5 דקות)"):
            try:
                result = _run_pipeline_sync(st.session_state["pipeline_input"])
                st.session_state["pipeline_result"] = result
                st.session_state["pipeline_complete"] = True
                st.rerun()
            except Exception as e:
                st.session_state["pipeline_running"] = False
                # Unwrap nested errors for a readable message
                cause = e
                while hasattr(cause, "__cause__") and cause.__cause__:
                    cause = cause.__cause__
                error_msg = str(cause) or str(e)
                st.error(f"❌ שגיאה בהרצת המנוע:\n\n`{error_msg}`")
                st.info("💡 בדוק שמפתח ה-API שהוזן תקין, ואז נסה שוב.")
                if st.button("🔄 נסה שוב"):
                    st.session_state.pop("pipeline_result", None)
                    st.session_state["pipeline_running"] = True
                    st.rerun()


def _render_outputs():
    """Render output documents."""
    result = st.session_state.get("pipeline_result")
    if not result:
        st.info("התהליך טרם הושלם")
        return

    st.header("📄 מסמכי ההגשה")

    output_dir = Path("./output")
    docx_files = list(output_dir.glob("*.docx"))
    xlsx_files = list(output_dir.glob("*.xlsx"))

    if docx_files:
        st.subheader("📝 טופס בקשה (Word)")
        for f in docx_files:
            with open(f, "rb") as file:
                st.download_button(
                    f"⬇️ הורד {f.name}",
                    file.read(),
                    file_name=f.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

    if xlsx_files:
        st.subheader("📊 תקציב (Excel)")
        for f in xlsx_files:
            with open(f, "rb") as file:
                st.download_button(
                    f"⬇️ הורד {f.name}",
                    file.read(),
                    file_name=f.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    # Show sections preview
    if result.get("sections"):
        st.subheader("👁️ תצוגה מקדימה")
        for section in result["sections"]:
            with st.expander(section["title_he"]):
                st.markdown(f"<div style='direction: rtl; text-align: right;'>{section['content_he']}</div>",
                           unsafe_allow_html=True)


def _render_evaluation():
    """Render Red Team evaluation results."""
    result = st.session_state.get("pipeline_result")
    if not result or not result.get("scores"):
        st.info("הערכה טרם בוצעה")
        return

    st.header("📊 הערכת איכות (Red Team)")
    st.metric("ציון כולל", f"{result.get('overall_score', 0):.1f}/100")

    cols = st.columns(len(result["scores"]))
    for i, score in enumerate(result["scores"]):
        with cols[i]:
            criterion_names = {
                "innovation": "חדשנות",
                "market": "שוק",
                "team": "צוות",
                "feasibility": "היתכנות",
                "grant_contribution": "תרומת מענק",
            }
            name = criterion_names.get(score["criterion"], score["criterion"])
            st.metric(name, f"{score['score']}/100")
            if score.get("feedback_he"):
                st.caption(score["feedback_he"][:100])

    st.info(f"סבבי הערכה: {result.get('evaluation_round', 0)}")


def _display_results_summary():
    """Display a summary of results."""
    result = st.session_state.get("pipeline_result", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ציון", f"{result.get('overall_score', 0):.0f}/100")
    with col2:
        st.metric("תקציב", f"₪{result.get('total_budget', 0):,.0f}")
    with col3:
        st.metric("מענק", f"₪{result.get('grant_amount', 0):,.0f}")


def _run_pipeline_sync(inputs: dict) -> dict:
    """Run the async pipeline in a dedicated thread with its own event loop.

    Streamlit ≥1.38 runs inside an async server, so calling asyncio.run()
    directly raises 'event loop is already running'.  Spawning a new thread
    gives us an isolated loop that is guaranteed to be idle.
    """
    result_holder: list = []
    exception_holder: list = []

    def worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_holder.append(loop.run_until_complete(_run_pipeline(inputs)))
        except Exception as exc:  # noqa: BLE001
            exception_holder.append(exc)
        finally:
            loop.close()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=600)  # 10-minute hard cap

    if exception_holder:
        raise exception_holder[0]
    if not result_holder:
        raise RuntimeError("Pipeline thread timed out after 10 minutes")
    return result_holder[0]


async def _run_pipeline(inputs: dict) -> dict:
    """Execute the grant pipeline."""
    # Set env vars from session state FIRST (before importing Settings)
    provider_keys = {
        "GROQ_API_KEY": "groq_api_key",
        "GEMINI_API_KEY": "gemini_api_key",
        "TOGETHER_API_KEY": "together_api_key",
        "OPENROUTER_API_KEY": "openrouter_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "OPENAI_API_KEY": "openai_api_key",
        "MISTRAL_API_KEY": "mistral_api_key",
    }
    for env_key, session_key in provider_keys.items():
        val = st.session_state.get(session_key, "")
        if val:
            os.environ[env_key] = val

    from src.graph.pipeline import compile_pipeline
    from src.graph.state import create_initial_state

    # Create initial state
    state = create_initial_state(**inputs)

    # Compile and run pipeline
    pipeline = compile_pipeline()
    result = await pipeline.ainvoke(state)

    return result


if __name__ == "__main__":
    main()
