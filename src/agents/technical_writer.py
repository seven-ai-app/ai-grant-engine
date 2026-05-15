"""Technical Writer Agent - PhD-level R&D descriptions from GitHub/code analysis."""

import logging
from .base_agent import BaseAgent
from ..graph.state import GrantState, ApplicationSection
from ..config.constants import APPLICATION_SECTIONS

logger = logging.getLogger(__name__)

TECHNICAL_WRITER_SYSTEM_PROMPT = """אתה כותב טכני ברמת דוקטורט, מומחה בניסוח פרקי מו"פ עבור בקשות מענקים לרשות החדשנות הישראלית.

## תפקידך:
לכתוב את הפרקים הטכנולוגיים של הבקשה ברמה אקדמית-תעשייתית גבוהה, תוך הדגשת עומק המו"פ, האתגרים הטכנולוגיים והחדשנות.

## עקרונות כתיבה:
1. **רמה אקדמית**: כתוב כאילו הבודק הוא פרופסור בתחום. השתמש במונחים מדויקים.
2. **חדשנות vs. הנדסה**: הבדל בין אתגר מו"פ (לא ידוע אם יעבוד) לבין עבודה הנדסית (ידוע שיעבוד, צריך לבנות).
3. **חסמי כניסה**: תאר מה מונע ממישהו אחר לעשות את אותו הדבר - זו "ההגנה" הטכנולוגית.
4. **מתודולוגיה**: פרט את הגישה המדעית - ניסויים, מדדי הצלחה, קריטריונים לקבלת החלטות.
5. **סיכונים טכנולוגיים**: הרשות מעריכה מיזמים שלוקחים סיכון טכנולוגי משמעותי.

## מבנה טיפוסי לכל סעיף:
- פתיחה: הצגת הבעיה/האתגר
- רקע: מצב הידע הקיים (State of the Art)
- הגישה שלנו: מה שונה ומדוע
- אתגרים ספציפיים: 3-5 חסמים טכנולוגיים מוגדרים היטב
- דרך פתרון: מתודולוגיה ואבני דרך
- מדדי הצלחה: KPIs טכניים מדידים

## הנחיות לסעיפים הטכנולוגיים:
- **חדשנות טכנולוגית**: תאר את הפער מהידע הקיים. מה לא קיים היום ומדוע.
- **תיאור המוצר**: ארכיטקטורה, רכיבים, ממשקים - ברמה טכנית גבוהה.
- **תוכנית מו"פ**: פרק למשימות (Work Packages), כל אחת עם מטרה, שיטה, תוצר.
- **אתגרים וסיכונים**: טבלת סיכונים (הסתברות x השפעה) עם Mitigation.
- **מתודולוגיה**: גישת הפיתוח (Agile/Waterfall/Hybrid), כלי בדיקה, מדדים.
- **קניין רוחני**: פטנטים צפויים, חופש פעולה (FTO), חסמי כניסה.
- **מצב נוכחי**: TRL (Technology Readiness Level), מה כבר הושג, מה נותר.

כתוב בעברית בלבד. רמה מקצועית גבוהה ביותר."""

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
                revision_notes = f"\n\nהערות לתיקון:\n" + "\n".join(existing["revision_notes"])

            user_prompt = f"""כתוב את הסעיף: {section_def['title_he']}

הקשר טכנולוגי מפורט:
{context}
{revision_notes}

כתוב תוכן מעמיק (500-1000 מילים). הדגש אתגרי מו"פ וחדשנות. עברית בלבד."""

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
                sections = [new_section if s["section_id"] == section_id else s for s in sections]
            else:
                sections.append(new_section)

        return {"sections": sections}

    def _build_technical_context(self, state: GrantState) -> str:
        parts = [
            f"שם המיזם: {state['startup_name']}",
            f"תיאור: {state['startup_description']}",
        ]

        ga = state.get("github_analysis", {})
        if ga:
            parts.append(f"\n=== ניתוח GitHub ===")
            parts.append(f"סיכום ארכיטקטורה: {ga.get('architecture_summary', 'לא זמין')}")

            for repo in ga.get("repositories", []):
                parts.append(f"\nRepository: {repo.get('name', 'N/A')}")
                parts.append(f"  תיאור: {repo.get('description', 'N/A')}")
                parts.append(f"  שפות: {', '.join(list(repo.get('languages', {}).keys())[:5])}")
                parts.append(f"  דפוסים: {', '.join(repo.get('patterns', []))}")
                parts.append(f"  קבצים: {repo.get('file_count', 0)}")
                if repo.get("top_dirs"):
                    parts.append(f"  תיקיות עיקריות: {', '.join(repo['top_dirs'][:10])}")

        if state.get("pitch_content"):
            # Extract technical portions from pitch
            pitch = state["pitch_content"]
            tech_keywords = ["algorithm", "architecture", "API", "ML", "AI", "patent",
                           "אלגוריתם", "ארכיטקטורה", "למידת מכונה", "פטנט"]
            relevant_lines = [
                line for line in pitch.split("\n")
                if any(kw.lower() in line.lower() for kw in tech_keywords)
            ]
            if relevant_lines:
                parts.append(f"\n=== תוכן טכני ממצגת ===")
                parts.append("\n".join(relevant_lines[:20]))

        return "\n".join(parts)
