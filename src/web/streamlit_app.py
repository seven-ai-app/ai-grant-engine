"""Streamlit web interface for the AI Grant Engine."""

import asyncio
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="AI Grant Engine - מנוע מענקים",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.markdown(
        """<h1 style='text-align: right; direction: rtl;'>
        🏛️ מנוע המענקים - AI Grant Engine
        </h1>
        <p style='text-align: right; direction: rtl; color: gray;'>
        מערכת אוטומטית לכתיבת בקשות מענק למסלול תנופה - רשות החדשנות
        </p>""",
        unsafe_allow_html=True,
    )

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ הגדרות")
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
        val = st.text_input(label, type="password", key=key)
        if val:
            st.session_state[key] = val

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

    st.header("🔄 מנוע המענקים בפעולה...")

    stages = [
        ("ingestion", "📥 קליטת מידע", "סריקת GitHub, מצגות ומסמכים"),
        ("matching", "✅ בדיקת התאמה", "אימות עמידה בתנאי סף"),
        ("drafting_strategy", "📊 אסטרטגיה", "כתיבת נרטיב עסקי ושיווקי"),
        ("drafting_technical", "🔬 כתיבה טכנית", "ניסוח פרקי מו\"פ וחדשנות"),
        ("financials", "💰 תקציב", "בניית תקציב אופטימלי"),
        ("evaluation", "🎯 הערכה", "בדיקת איכות (Red Team)"),
        ("output", "📄 הפקת מסמכים", "יצירת Word ו-Excel"),
    ]

    current = st.session_state.get("current_stage", "ingestion")
    for stage_id, label, desc in stages:
        if stage_id == current:
            st.markdown(f"⏳ **{label}** - {desc}")
            st.progress(0.5)
        elif stages.index((stage_id, label, desc)) < [s[0] for s in stages].index(current):
            st.markdown(f"✅ ~~{label}~~")
        else:
            st.markdown(f"⬜ {label}")

    # Run pipeline
    if st.session_state.get("pipeline_input") and not st.session_state.get("pipeline_result"):
        with st.spinner("מעבד..."):
            result = asyncio.run(_run_pipeline(st.session_state["pipeline_input"]))
            st.session_state["pipeline_result"] = result
            st.session_state["pipeline_complete"] = True
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


async def _run_pipeline(inputs: dict) -> dict:
    """Execute the grant pipeline."""
    import os
    from ..config.settings import Settings
    from ..graph.pipeline import compile_pipeline
    from ..graph.state import create_initial_state

    # Set env vars from session state
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
        val = st.session_state.get(session_key)
        if val:
            os.environ[env_key] = val

    # Create initial state
    state = create_initial_state(**inputs)

    # Compile and run pipeline
    pipeline = compile_pipeline()
    result = await pipeline.ainvoke(state)

    return result


if __name__ == "__main__":
    main()
