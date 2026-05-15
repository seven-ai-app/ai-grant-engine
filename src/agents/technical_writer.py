"""Technical Writer Agent - PhD-level R&D descriptions.

Generates all sections assigned to the 'technical_writer' agent in APPLICATION_SECTIONS,
using the official Tnufa form instructions (instructions_he) as the writing guide.
Also produces structured rd_tasks, capability_table, and competitor_table lists.
"""

import logging
import json
from .base_agent import BaseAgent
from ..graph.state import GrantState, ApplicationSection
from ..config.constants import APPLICATION_SECTIONS

logger = logging.getLogger(__name__)

TECHNICAL_WRITER_SYSTEM_PROMPT = """אתה כותב טכני-מדעי ברמת דוקטורט, מומחה בניסוח פרקי מו"פ עבור בקשות מענקים לרשות החדשנות הישראלית, מסלול תנופה.

## תפקידך:
לכתוב את הפרקים הטכנולוגיים של הבקשה ברמה אקדמית-תעשייתית גבוהה - מדויק, עמוק, ומשכנע.

## עקרונות כתיבה מחייבים:
1. **ספציפיות טכנית**: תאר אלגוריתמים ספציפיים, ארכיטקטורה, שפות תכנות, ספריות, מסגרות עבודה.
2. **אתגרי מו"פ אמיתיים**: הבדל בין חדשנות (לא ידוע אם יעבוד - זה מו"פ) להנדסה (ידוע שיעבוד).
3. **TRL**: ציין רמת בשלות טכנולוגית (1-9) בהתאם להנחיות.
4. **ניסוח אקדמי**: כאילו הבודק הוא פרופסור בתחום - מונחים מדויקים ועמוקים.
5. **חסמי כניסה**: תאר מה מונע ממתחרים לשכפל - זו ה"הגנה" הטכנולוגית.

## מבנה טיפוסי לסעיף:
- מצב הידע הקיים (State of the Art) - מה קיים ומה חסר
- הגישה הייחודית שלנו - מה שונה ולמה
- אתגרים טכנולוגיים ספציפיים (3-5) עם תיאור מדעי מדויק
- מתודולוגיה: ניסויים, מדדי הצלחה, קריטריונים
- מדדי ביצוע כמותיים (KPIs)

## כללים:
- כתוב בעברית בלבד.
- אל תכלול את שם הסעיף - רק את התוכן.
- אסור לכתוב "אנחנו משתמשים ב-AI/ML" ללא פירוט ספציפי - מה בדיוק, איזה אלגוריתם, באיזו ארכיטקטורה.
- אם חסר מידע ספציפי - השתמש בידע הטכני שלך לייצור תוכן רלוונטי ומשכנע לתחום."""


TECHNICAL_SECTIONS = [
    s for s in APPLICATION_SECTIONS if s["agent"] == "technical_writer"
]


class TechnicalWriterAgent(BaseAgent):
    name = "technical_writer"
    task_type = "hebrew"

    async def run(self, state: GrantState) -> dict:
        context = self._build_technical_context(state)
        sections = list(state.get("sections", []))

        for section_def in TECHNICAL_SECTIONS:
            section_id = section_def["id"]
            existing = next((s for s in sections if s["section_id"] == section_id), None)

            if existing and existing["status"] == "approved":
                continue

            revision_notes = ""
            if existing and existing.get("revision_notes"):
                revision_notes = "\n\nהערות לתיקון:\n" + "\n".join(existing["revision_notes"])

            max_words = section_def.get("max_words", 600)
            instructions = section_def.get("instructions_he", "")

            user_prompt = f"""כתוב את הסעיף: **{section_def['title_he']}**

## הנחיות לסעיף זה:
{instructions}

## מידע טכנולוגי על המיזם:
{context}
{revision_notes}

## הנחיות כתיבה:
- כתוב תוכן טכני מעמיק בעברית, {max_words}-{max_words + 200} מילים.
- היה ספציפי ומדויק - שמות אלגוריתמים, ארכיטקטורות, שפות, ספריות.
- הדגש אתגרי מו"פ אמיתיים ולא רק עבודה הנדסית.
- אל תכתוב את שם הסעיף - רק תוכן."""

            content = await self._generate(
                system_prompt=TECHNICAL_WRITER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.6,
                max_tokens=4000,
            )

            new_section = ApplicationSection(
                section_id=section_id,
                title_he=section_def["title_he"],
                content_he=content,
                status="revised" if existing else "draft",
                revision_notes=[],
            )

            if existing:
                sections = [
                    new_section if s["section_id"] == section_id else s
                    for s in sections
                ]
            else:
                sections.append(new_section)

        # Generate structured tables
        rd_tasks = await self._generate_rd_tasks(state, context)
        capability_table = await self._generate_capability_table(state, context)

        return {
            "sections": sections,
            "rd_tasks": rd_tasks,
            "capability_table": capability_table,
        }

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def _build_technical_context(self, state: GrantState) -> str:
        parts = [
            f"שם המיזם: {state['startup_name']}",
            f"תיאור: {state['startup_description']}",
        ]

        ga = state.get("github_analysis", {})
        if ga:
            parts.append("\n=== ניתוח GitHub ===")
            arch = ga.get("architecture_summary", "")
            if arch:
                parts.append(f"ארכיטקטורה: {arch}")
            for repo in ga.get("repositories", [])[:4]:
                parts.append(f"\nRepository: {repo.get('name', 'N/A')}")
                parts.append(f"  תיאור: {repo.get('description', '')}")
                langs = list(repo.get("languages", {}).keys())[:6]
                if langs:
                    parts.append(f"  שפות: {', '.join(langs)}")
                patterns = repo.get("patterns", [])
                if patterns:
                    parts.append(f"  דפוסים טכנולוגיים: {', '.join(patterns)}")
                top_dirs = repo.get("top_dirs", [])[:8]
                if top_dirs:
                    parts.append(f"  מודולים עיקריים: {', '.join(top_dirs)}")
                parts.append(f"  מספר קבצים: {repo.get('file_count', 0)}")

        if state.get("pitch_content"):
            pitch = state["pitch_content"]
            # Pull lines with technical signals
            tech_keywords = [
                "algorithm", "architecture", "API", "ML", "AI", "model", "neural",
                "database", "cloud", "latency", "accuracy", "precision",
                "אלגוריתם", "ארכיטקטורה", "למידת מכונה", "רשת נוירונית",
                "דגם", "דיוק", "ביצועים", "פלטפורמה", "מנוע", "עיבוד",
            ]
            relevant_lines = [
                line.strip() for line in pitch.split("\n")
                if line.strip() and any(kw.lower() in line.lower() for kw in tech_keywords)
            ]
            if relevant_lines:
                parts.append("\n=== תוכן טכני ממסמכים ===")
                parts.append("\n".join(relevant_lines[:30]))

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Structured table generators
    # ------------------------------------------------------------------

    async def _generate_rd_tasks(self, state: GrantState, context: str) -> list[dict]:
        """Generate a structured list of 5-7 R&D tasks."""
        prompt = f"""בהתבסס על המידע הטכנולוגי הבא, צור רשימה של 6 משימות מו"פ עבור תוכנית עבודה של 12 חודשים.

{context}

החזר תשובה בפורמט JSON בלבד - מערך של אובייקטים, כל אחד עם המפתחות:
- "task_name": שם המשימה בעברית (5-8 מילים)
- "description": תיאור מפורט עם 4 שלבים (שורות נפרדות עם מספור 1. 2. 3. 4.)
- "start_mm_yy": חודש התחלה (פורמט MM/YY, התחל מ-01/25)
- "end_mm_yy": חודש סיום (פורמט MM/YY)

דאג לכסות: מחקר בסיסי, פיתוח אלגוריתמים, POC, אינטגרציה, בדיקות ביצועים.
מרחק בין התחלה לסיום של כל משימה: 2-3 חודשים.
JSON בלבד - ללא הסברים נוספים."""

        raw = await self._generate(
            TECHNICAL_WRITER_SYSTEM_PROMPT, prompt, temperature=0.5, max_tokens=2000
        )
        return self._parse_json_list(raw, fallback=self._default_rd_tasks())

    async def _generate_capability_table(self, state: GrantState, context: str) -> list[dict]:
        """Generate a capability gap table."""
        prompt = f"""בהתבסס על המיזם הבא, צור טבלת יכולות המציגה מצב נוכחי ויעד בסיום הפרויקט.

{context}

החזר JSON בלבד - מערך של 6-8 אובייקטים, כל אחד עם המפתחות:
- "capability": שם היכולת בעברית
- "current_state": מצב נוכחי (קצר - 5-10 מילים)
- "target_state": מצב יעד בסיום הפרויקט (קצר - 5-10 מילים)

JSON בלבד."""

        raw = await self._generate(
            TECHNICAL_WRITER_SYSTEM_PROMPT, prompt, temperature=0.5, max_tokens=1500
        )
        return self._parse_json_list(raw, fallback=self._default_capability_table())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_list(raw: str, fallback: list) -> list:
        """Try to parse JSON from LLM output; return fallback on failure."""
        if not raw:
            return fallback
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        # Try to find JSON array inside the text
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            try:
                parsed = json.loads(text[start : end + 1])
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        logger.warning("Could not parse JSON list from LLM output; using fallback.")
        return fallback

    @staticmethod
    def _default_rd_tasks() -> list[dict]:
        return [
            {
                "task_name": "מחקר בסיסי ואפיון דרישות",
                "description": "1. סקירת ספרות ומצב הידע הקיים\n2. אפיון דרישות פונקציונליות ולא-פונקציונליות\n3. הגדרת מדדי הצלחה כמותיים\n4. תכנון ארכיטקטורה ראשונית",
                "start_mm_yy": "01/25",
                "end_mm_yy": "02/25",
            },
            {
                "task_name": "פיתוח אלגוריתם ליבה",
                "description": "1. עיצוב ומימוש האלגוריתם המרכזי\n2. בדיקות יחידה ואינטגרציה ראשוניות\n3. אופטימיזציה של ביצועים\n4. תיעוד טכני מפורט",
                "start_mm_yy": "02/25",
                "end_mm_yy": "04/25",
            },
            {
                "task_name": "בניית אב-טיפוס (POC)",
                "description": "1. הקמת סביבת פיתוח ובדיקות\n2. מימוש POC מלא עם ממשק משתמש בסיסי\n3. בדיקות פונקציונליות על נתוני דמה\n4. תיקוף ראשוני מול משתמשי מפתח",
                "start_mm_yy": "04/25",
                "end_mm_yy": "06/25",
            },
            {
                "task_name": "אינטגרציה ובדיקות מערכת",
                "description": "1. שילוב כל הרכיבים לפלטפורמה אחת\n2. בדיקות עומס וביצועים\n3. אבטחת מידע ובדיקות חדירה\n4. תיקון ליקויים ואופטימיזציה",
                "start_mm_yy": "06/25",
                "end_mm_yy": "08/25",
            },
            {
                "task_name": "תיקוף שוק ופיילוט",
                "description": "1. הכנת סביבת פיילוט ללקוחות נבחרים\n2. הפעלת פיילוט עם 3-5 לקוחות ראשונים\n3. איסוף משוב ומדדי שימוש\n4. שיפורים מבוססי משוב",
                "start_mm_yy": "08/25",
                "end_mm_yy": "10/25",
            },
            {
                "task_name": "הכנה לגרסה מסחרית ראשונה",
                "description": "1. גיבוש גרסה יציבה ומוכנה לייצור\n2. תיעוד מלא ומדריכי משתמש\n3. הכנת תשתיות Cloud לפריסה\n4. הגשת בקשת פטנט על חידושי הליבה",
                "start_mm_yy": "10/25",
                "end_mm_yy": "12/25",
            },
        ]

    @staticmethod
    def _default_capability_table() -> list[dict]:
        return [
            {"capability": "אלגוריתם ליבה", "current_state": "קונספט ראשוני בלבד", "target_state": "אלגוריתם מיושם ומאומת"},
            {"capability": "ארכיטקטורת תוכנה", "current_state": "תכנון ראשוני על נייר", "target_state": "ארכיטקטורה מלאה ומיושמת"},
            {"capability": "אב-טיפוס (POC)", "current_state": "לא קיים", "target_state": "POC פועל עם נתונים אמיתיים"},
            {"capability": "תשתיות Cloud", "current_state": "אין תשתית", "target_state": "פריסה מלאה בענן"},
            {"capability": "קניין רוחני", "current_state": "אין פטנט", "target_state": "בקשת פטנט מוגשת"},
            {"capability": "תיקוף שוק", "current_state": "שיחות ראשוניות בלבד", "target_state": "פיילוט עם 3+ לקוחות"},
        ]
