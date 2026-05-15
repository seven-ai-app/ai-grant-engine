"""Strategist Agent - Market narrative and Innovation Authority alignment.

Generates all sections assigned to the 'strategist' agent in APPLICATION_SECTIONS,
using the official Tnufa form instructions (instructions_he) as the writing guide.
"""

import logging
from .base_agent import BaseAgent
from ..graph.state import GrantState, ApplicationSection
from ..config.constants import APPLICATION_SECTIONS

logger = logging.getLogger(__name__)

STRATEGIST_SYSTEM_PROMPT = """אתה יועץ אסטרטגי ומומחה כתיבת מענקים בכיר, עם ניסיון של 15 שנה בהגשת בקשות מוצלחות לרשות החדשנות הישראלית, מסלול תנופה.

## תפקידך:
לכתוב את הסעיפים האסטרטגיים-עסקיים של הבקשה ברמה המקצועית הגבוהה ביותר, בהתאם להנחיות הסעיף הספציפי.

## עקרונות כתיבה מחייבים:
1. **ספציפיות**: כל טענה חייבת להיות מגובה בנתונים מספריים, שמות מתחרים, נתוני שוק. אסור לכתוב באופן גנרי.
2. **שפה**: עברית אקדמית-תעשייתית. מדויקת, שכנועית, ללא הגזמות ריקות.
3. **קריטריונים**: הרשות מעריכה: חדשנות (30%), שוק (20%), צוות (20%), היתכנות (15%), תרומת מענק (15%).
4. **מבנה**: כל סעיף פותח בטענה מרכזית ברורה, מגובה בעובדות ונתונים, ונחתם בהשלכה ישירה על המיזם.

## מילות מפתח חיוניות שיש לשלב באופן טבעי:
- "הורדת סיכון טכנולוגי" (Technology De-risking)
- "חופש פעולה" (Freedom to Operate)
- "קפיצת מדרגה" (Technological Leap)
- "פוטנציאל גלובלי"
- "תרומה לכלכלה הישראלית"
- "הוכחת היתכנות" (POC)
- "יכולת הגנה" (Defensibility)

## כללים:
- כתוב בעברית בלבד.
- אל תכלול את שם הסעיף עצמו - רק את התוכן.
- השתמש בנתוני שוק אמינים (Gartner, IDC, Statista, CB Insights) כשמציין נתונים.
- אם חסר מידע ספציפי על המיזם - השתמש בתחום הידע שלך ליצירת תוכן רלוונטי ומשכנע.
- כתוב בגוף ראשון רבים ("אנו", "המיזם שלנו") עבור סעיפים שתואמים לכך."""


STRATEGIST_SECTIONS = [
    s for s in APPLICATION_SECTIONS if s["agent"] == "strategist"
]


class StrategistAgent(BaseAgent):
    name = "strategist"
    task_type = "hebrew"

    async def run(self, state: GrantState) -> dict:
        context = self._build_context(state)
        sections = list(state.get("sections", []))

        for section_def in STRATEGIST_SECTIONS:
            section_id = section_def["id"]
            existing = next((s for s in sections if s["section_id"] == section_id), None)

            # Skip if already approved
            if existing and existing["status"] == "approved":
                continue

            revision_notes = ""
            if existing and existing.get("revision_notes"):
                revision_notes = "\n\nהערות לתיקון מסבב קודם:\n" + "\n".join(existing["revision_notes"])

            max_words = section_def.get("max_words", 500)
            instructions = section_def.get("instructions_he", "")

            user_prompt = f"""כתוב את הסעיף: **{section_def['title_he']}**

## הנחיות לסעיף זה:
{instructions}

## מידע על המיזם:
{context}
{revision_notes}

## הנחיות כתיבה:
- כתוב תוכן מקצועי ומשכנע בעברית, {max_words}-{max_words + 200} מילים.
- היה ספציפי לחלוטין למיזם זה - אסור לכתוב בצורה גנרית.
- כלול נתונים מספריים, שמות ספציפיים, הפניות לשוק.
- אל תכתוב את שם הסעיף עצמו - רק את התוכן."""

            content = await self._generate(
                system_prompt=STRATEGIST_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.65,
                max_tokens=3500,
            )

            new_section = ApplicationSection(
                section_id=section_id,
                title_he=section_def["title_he"],
                content_he=content,
                status="revised" if existing else "draft",
                revision_notes=[],
            )

            # Update or append
            if existing:
                sections = [
                    new_section if s["section_id"] == section_id else s
                    for s in sections
                ]
            else:
                sections.append(new_section)

        # Generate auxiliary strategic fields
        market_analysis = await self._generate_market_analysis(context)
        competitive = await self._generate_competitive_landscape(context)

        return {
            "sections": sections,
            "market_analysis_he": market_analysis,
            "competitive_landscape_he": competitive,
            "unfair_advantage_he": self._extract_unfair_advantage(state),
        }

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def _build_context(self, state: GrantState) -> str:
        parts = [
            f"שם המיזם: {state['startup_name']}",
            f"סוג ישות: {'יזם פרטי' if state.get('entity_type') == 'private_entrepreneur' else 'חברה חדשה'}",
            f"תיאור המיזם: {state['startup_description']}",
        ]

        if state.get("pitch_content"):
            parts.append(f"\n=== תוכן שחולץ ממסמכים/מצגת ===\n{state['pitch_content'][:4000]}")

        if state.get("github_analysis"):
            ga = state["github_analysis"]
            arch = ga.get("architecture_summary", "")
            if arch:
                parts.append(f"\n=== ניתוח טכני (GitHub) ===\nארכיטקטורה: {arch}")
            langs = ga.get("languages", {})
            if langs:
                parts.append(f"שפות תכנות: {', '.join(list(langs.keys())[:6])}")
            for repo in ga.get("repositories", [])[:3]:
                name = repo.get("name", "")
                desc = repo.get("description", "")
                patterns = ", ".join(repo.get("patterns", []))
                if name:
                    parts.append(f"Repo '{name}': {desc}. דפוסים: {patterns}")

        if state.get("team_profiles"):
            team_lines = [
                f"  - {m['name']} ({m['role']}): {m['experience_summary']}"
                for m in state["team_profiles"]
            ]
            parts.append("\n=== צוות ===\n" + "\n".join(team_lines))

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Auxiliary generators
    # ------------------------------------------------------------------

    async def _generate_market_analysis(self, context: str) -> str:
        prompt = f"""בהתבסס על המידע הבא, כתוב ניתוח שוק תמציתי (150-200 מילים) הכולל:
- גודל שוק (TAM/SAM/SOM) עם מספרים ספציפיים
- קצב גידול שנתי (CAGR)
- מגמות עיקריות בשוק
- כאבים עיקריים של לקוחות היעד

{context}

עברית בלבד. נתונים ספציפיים בלבד - ללא תוכן גנרי."""
        return await self._generate(
            STRATEGIST_SYSTEM_PROMPT, prompt, temperature=0.6, max_tokens=1000
        )

    async def _generate_competitive_landscape(self, context: str) -> str:
        prompt = f"""בהתבסס על המידע הבא, כתוב ניתוח תחרותי תמציתי (150-200 מילים) הכולל:
- שמות ספציפיים של מתחרים ישירים ועקיפים
- חולשות עיקריות של המתחרים הקיימים
- הבידול הייחודי של המיזם שלנו ביחס לכל מתחרה
- סיבה לכך שהלקוח יבחר בנו

{context}

עברית בלבד. ספציפי ומדויק - ציין שמות חברות ואתרים."""
        return await self._generate(
            STRATEGIST_SYSTEM_PROMPT, prompt, temperature=0.6, max_tokens=1000
        )

    def _extract_unfair_advantage(self, state: GrantState) -> str:
        ga = state.get("github_analysis", {})
        if ga.get("repositories"):
            patterns = set()
            for repo in ga["repositories"]:
                patterns.update(repo.get("patterns", []))
            if patterns:
                return f"יתרון טכנולוגי מוכח מניתוח קוד: {', '.join(patterns)}"
        desc = state.get("startup_description", "")
        return desc[:200] if desc else ""
