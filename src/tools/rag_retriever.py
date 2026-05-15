"""RAG retriever for Tnufa knowledge base and eligibility checking."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Embedded knowledge for eligibility (no vector DB required for basic checks)
TNUFA_ELIGIBILITY_RULES = {
    "entity_types_allowed": ["private_entrepreneur", "new_company"],
    "max_prior_funding": 3_000_000,
    "residency_requirement": "israel",
    "no_prior_commercial_activity": True,
    "max_team_size": None,
    "sector_restrictions": None,
}

TNUFA_DISQUALIFIERS = [
    "prior_tnufa_grant_same_project",
    "active_grant_same_project",
    "commercial_revenue_exceeds_threshold",
    "non_resident_majority",
]


async def check_eligibility(
    entity_type: str,
    startup_description: str,
    github_analysis: dict,
) -> tuple[bool, list[str]]:
    """Check basic eligibility for Tnufa track."""
    notes = []
    is_eligible = True

    # Check entity type
    if entity_type not in TNUFA_ELIGIBILITY_RULES["entity_types_allowed"]:
        notes.append(f"סוג ישות '{entity_type}' אינו מתאים למסלול תנופה")
        is_eligible = False
    else:
        notes.append(f"סוג ישות '{entity_type}' - מתאים למסלול")

    # Check if project has technological innovation (basic heuristic)
    if github_analysis:
        patterns = []
        for repo in github_analysis.get("repositories", []):
            patterns.extend(repo.get("patterns", []))

        if "machine_learning" in patterns or "algorithmic" in patterns:
            notes.append("זוהתה חדשנות טכנולוגית בקוד (ML/אלגוריתמיקה)")
        elif patterns:
            notes.append(f"דפוסי פיתוח שזוהו: {', '.join(set(patterns))}")
        else:
            notes.append("לא זוהו דפוסי חדשנות בולטים - ייתכן שנדרש פירוט נוסף")

    # Basic description check
    if len(startup_description) < 50:
        notes.append("תיאור המיזם קצר מדי - מומלץ להרחיב")
        # Not a disqualifier but a warning

    if is_eligible:
        notes.append("המיזם עומד בתנאי הסף הבסיסיים של מסלול תנופה")

    return is_eligible, notes


async def retrieve_relevant_procedures(query: str, top_k: int = 3) -> list[dict]:
    """Retrieve relevant procedure sections from knowledge base.

    Falls back to hardcoded knowledge if ChromaDB is not available.
    """
    try:
        return await _retrieve_from_chromadb(query, top_k)
    except Exception as e:
        logger.warning(f"ChromaDB not available, using hardcoded knowledge: {e}")
        return _get_hardcoded_procedures(query)


async def _retrieve_from_chromadb(query: str, top_k: int) -> list[dict]:
    """Retrieve from ChromaDB vector store."""
    import chromadb
    from ..config.settings import Settings

    settings = Settings()
    client = chromadb.PersistentClient(path=settings.chroma_db_path)

    try:
        collection = client.get_collection("tnufa_procedures")
    except Exception:
        return _get_hardcoded_procedures(query)

    results = collection.query(query_texts=[query], n_results=top_k)

    docs = []
    for i, doc in enumerate(results["documents"][0]):
        docs.append({
            "content": doc,
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "score": results["distances"][0][i] if results["distances"] else 0,
        })
    return docs


def _get_hardcoded_procedures(query: str) -> list[dict]:
    """Fallback hardcoded Tnufa procedure knowledge."""
    procedures = [
        {
            "content": """מסלול תנופה - הוצאות מוכרות:
            - קבלני משנה: עד 300 ש"ח לשעה, כולל מפתחים, מעצבים, יועצי טכנולוגיה
            - חומרים ורכיבים: חומרי גלם, רכיבים מתכלים לבניית אב-טיפוס
            - קניין רוחני: עורכי פטנטים, רישום פטנטים בארץ ובחו"ל
            - פיתוח עסקי: יועצי שיווק, תערוכות מקצועיות בחו"ל
            - ציוד: פחת 33% לשנה על ציוד ייעודי""",
            "metadata": {"section": "eligible_expenses", "procedure": "200-02"},
        },
        {
            "content": """מסלול תנופה - הוצאות לא מוכרות:
            - שכר יזמים או עובדים קבועים של המיזם
            - הוצאות תקורה: שכירות, חשמל, מים, אינטרנט
            - מע"מ (למעט מלכ"רים)
            - הוצאות שיווק כלליות (שאינן תערוכות מקצועיות)
            - רכישת ציוד (רק פחת מוכר)""",
            "metadata": {"section": "forbidden_expenses", "procedure": "200-02"},
        },
        {
            "content": """קריטריוני הערכה של בודקי הרשות:
            1. חדשנות טכנולוגית - האם קיים סיכון מו"פ אמיתי? האם הפתרון דורש מחקר ופיתוח?
            2. פוטנציאל עסקי - גודל שוק עולמי, יכולת צמיחה, מודל עסקי
            3. איכות הצוות - ניסיון רלוונטי, רקע אקדמי, יכולת ביצוע
            4. היתכנות - ריאליסטיות של תוכנית העבודה, אבני דרך ברורות
            5. תרומת המענק - האם המענק מהווה גורם מאפשר קריטי""",
            "metadata": {"section": "evaluation_criteria", "procedure": "tnufa"},
        },
        {
            "content": """תנאי סף למסלול תנופה:
            - יזם פרטי או חברה חדשה (ללא פעילות מסחרית קודמת)
            - תושב/ת ישראל
            - לא גייס מעל 3 מיליון ש"ח בעבר
            - פרויקט בעל חדשנות טכנולוגית (לא רק שיפור תוספתי)
            - תקציב מבוקש עד 250,000 ש"ח
            - תקופת ביצוע עד 12 חודשים""",
            "metadata": {"section": "eligibility", "procedure": "tnufa"},
        },
    ]
    return procedures
