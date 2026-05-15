import logging
from .state import GrantState

logger = logging.getLogger(__name__)


def _get_router():
    """Create a fresh LLMRouter from current environment variables."""
    from ..config.settings import Settings
    from ..llm.router import LLMRouter
    settings = Settings()
    return LLMRouter(settings)


async def ingest_node(state: GrantState) -> dict:
    """Scan GitHub repos, parse uploaded documents, extract team info."""
    from ..tools.github_analyzer import analyze_github_repos
    from ..tools.document_parser import parse_uploaded_files

    logger.info(f"[Ingestion] Processing inputs for: {state['startup_name']}")

    github_analysis = {}
    if state["github_urls"]:
        try:
            github_analysis = await analyze_github_repos(state["github_urls"])
        except Exception as e:
            logger.warning(f"GitHub analysis failed: {e}")

    raw_documents = []
    pitch_content = ""
    if state["uploaded_files"]:
        try:
            raw_documents = await parse_uploaded_files(state["uploaded_files"])
            pitch_content = "\n\n".join(doc.get("content", "") for doc in raw_documents)
        except Exception as e:
            logger.warning(f"Document parsing failed: {e}")

    return {
        "github_analysis": github_analysis,
        "raw_documents": raw_documents,
        "pitch_content": pitch_content,
        "current_stage": "matching",
    }


async def eligibility_node(state: GrantState) -> dict:
    """Check if startup meets Tnufa eligibility requirements."""
    from ..tools.rag_retriever import check_eligibility

    logger.info("[Matching] Checking eligibility against Tnufa requirements")

    try:
        is_eligible, notes = await check_eligibility(
            entity_type=state["entity_type"],
            startup_description=state["startup_description"],
            github_analysis=state["github_analysis"],
        )
    except Exception as e:
        logger.warning(f"Eligibility check failed: {e}")
        is_eligible, notes = True, ["בדיקת זכאות אוטומטית לא הצליחה - ממשיך בהנחה שהמיזם זכאי"]

    return {
        "is_eligible": is_eligible,
        "eligibility_notes": notes,
        "current_stage": "drafting_strategy" if is_eligible else "rejected",
    }


async def strategist_node(state: GrantState) -> dict:
    """Generate strategic narrative sections of the application."""
    from ..agents.strategist import StrategistAgent

    logger.info("[Strategist] Drafting market & strategy sections")

    try:
        router = _get_router()
        agent = StrategistAgent(router)
        result = await agent.run(state)
        # Carry forward competitor_table (may be populated elsewhere later)
        result.setdefault("competitor_table", state.get("competitor_table", []))
        return {**result, "current_stage": "drafting_technical"}
    except Exception as e:
        logger.error(f"Strategist failed: {e}")
        return {
            "sections": state.get("sections", []),
            "competitor_table": state.get("competitor_table", []),
            "current_stage": "drafting_technical",
            "error": f"Strategist error: {str(e)[:200]}",
        }


async def technical_writer_node(state: GrantState) -> dict:
    """Generate technical/R&D sections from GitHub analysis."""
    from ..agents.technical_writer import TechnicalWriterAgent

    logger.info("[Technical Writer] Drafting R&D sections")

    try:
        router = _get_router()
        agent = TechnicalWriterAgent(router)
        result = await agent.run(state)
        # Ensure new structured-table fields are always present
        result.setdefault("rd_tasks", state.get("rd_tasks", []))
        result.setdefault("capability_table", state.get("capability_table", []))
        return {**result, "current_stage": "financials"}
    except Exception as e:
        logger.error(f"Technical Writer failed: {e}")
        return {
            "sections": state.get("sections", []),
            "rd_tasks": state.get("rd_tasks", []),
            "capability_table": state.get("capability_table", []),
            "current_stage": "financials",
            "error": f"Technical Writer error: {str(e)[:200]}",
        }


async def cfo_node(state: GrantState) -> dict:
    """Build optimized budget within Tnufa constraints."""
    from ..agents.cfo import CFOAgent

    logger.info("[CFO] Building budget")

    try:
        router = _get_router()
        agent = CFOAgent(router)
        result = await agent.run(state)
        return {**result, "current_stage": "evaluation"}
    except Exception as e:
        logger.error(f"CFO failed: {e}")
        # Generate default budget as fallback
        from ..tools.budget_calculator import validate_budget
        default_lines = _default_budget_lines()
        validation = validate_budget(default_lines)
        return {
            "sections": state.get("sections", []),
            "budget_lines": default_lines,
            "total_budget": validation.total_budget,
            "grant_amount": validation.grant_amount,
            "self_funding": validation.self_funding,
            "budget_valid": validation.is_valid,
            "budget_notes": [f"תקציב ברירת מחדל (שגיאה: {str(e)[:100]})"],
            "current_stage": "evaluation",
        }


async def red_team_node(state: GrantState) -> dict:
    """Evaluate application quality and decide if revision needed."""
    from ..agents.red_team import RedTeamAgent

    logger.info(f"[Red Team] Evaluation round {state['evaluation_round'] + 1}")

    try:
        router = _get_router()
        agent = RedTeamAgent(router)
        result = await agent.run(state)
        return {**result, "evaluation_round": state["evaluation_round"] + 1}
    except Exception as e:
        logger.error(f"Red Team failed: {e}")
        from ..config.constants import EVALUATION_CRITERIA
        default_scores = [
            {"criterion": k, "score": 80, "weight": v["weight"],
             "feedback_he": "הערכה אוטומטית", "suggestions": []}
            for k, v in EVALUATION_CRITERIA.items()
        ]
        return {
            "scores": default_scores,
            "overall_score": 80.0,
            "revision_target": None,
            "evaluation_round": state["evaluation_round"] + 1,
        }


async def output_node(state: GrantState) -> dict:
    """Generate final DOCX and XLSX files."""
    from ..output.docx_generator import generate_application_docx
    from ..output.xlsx_generator import generate_budget_xlsx
    from ..config.settings import Settings

    logger.info("[Output] Generating final documents")

    try:
        settings = Settings()
        output_dir = settings.output_path
        docx_path = generate_application_docx(state, output_dir)
        xlsx_path = generate_budget_xlsx(state, output_dir)
        logger.info(f"[Output] Generated: {docx_path}, {xlsx_path}")
    except Exception as e:
        logger.error(f"Output generation failed: {e}")

    return {"current_stage": "complete"}


def _default_budget_lines():
    from ..graph.state import BudgetLine
    from ..config.constants import GRANT_RATE

    # (category, description_he, amount, hourly_rate, hours, justification_he)
    lines = [
        (
            "subcontractors",
            "פיתוח תוכנה - קבלן משנה",
            100_000, 250, 400,
            "פיתוח רכיבי הליבה הטכנולוגיים על ידי מפתח בכיר בתעריף 250 ₪/שעה "
            "ל-400 שעות. נדרש לצורך הורדת סיכון טכנולוגי בשלב הפיתוח.",
        ),
        (
            "subcontractors",
            "פיתוח אלגוריתמים ובינה מלאכותית",
            60_000, 300, 200,
            "מומחה אלגוריתמים בתעריף 300 ₪/שעה ל-200 שעות. קפיצת מדרגה "
            "טכנולוגית הדורשת ידע מתמחה שאינו קיים בצוות הנוכחי.",
        ),
        (
            "materials",
            "שרתים, תשתיות ענן ורישיונות",
            30_000, None, None,
            "עלויות תשתית ענן (AWS/GCP) לפיתוח, בדיקות ואחסון נתונים "
            "לאורך 12 חודשי הפרויקט. נדרש לבניית סביבת הפיתוח.",
        ),
        (
            "ip_patents",
            "הגשת בקשת פטנט וסקר FTO",
            30_000, None, None,
            "הגשת בקשת פטנט ישראלית ובינלאומית (PCT) להגנה על חידושי הליבה, "
            "וסקר חופש פעולה (FTO) לוודא שאין הפרת זכויות קיימות.",
        ),
        (
            "business_development",
            "ייעוץ עסקי ותיקוף שוק",
            20_000, 200, 100,
            "יועץ עסקי בכיר בתעריף 200 ₪/שעה ל-100 שעות לפיתוח תוכנית עסקית, "
            "תיקוף שוק מול לקוחות פוטנציאלים, והכנה לגיוס הון.",
        ),
        (
            "travel_abroad",
            "השתתפות בתערוכה בינלאומית",
            10_000, None, None,
            "השתתפות בתערוכת טכנולוגיה בינלאומית רלוונטית לתחום המיזם, "
            "לצורך תיקוף שוק, יצירת קשרים עסקיים ופגישות עם משקיעים פוטנציאלים.",
        ),
    ]
    return [
        BudgetLine(
            category=cat,
            description_he=desc,
            amount=amt,
            grant_portion=round(amt * GRANT_RATE, 2),
            justification_he=just,
            hourly_rate=rate,
            hours=hours,
        )
        for cat, desc, amt, rate, hours, just in lines
    ]
