"""Strategist Agent - Market narrative and Innovation Authority alignment."""

import logging
from .base_agent import BaseAgent
from ..graph.state import GrantState, ApplicationSection
from ..config.constants import APPLICATION_SECTIONS

logger = logging.getLogger(__name__)

STRATEGIST_SYSTEM_PROMPT = """אתה יועץ אסטרטגי מומחה בכתיבת בקשות מענקים לרשות החדשנות הישראלית, מסלול "תנופה" (Ideation).

תפקידך: לכתוב את הסעיפים האסטרטגיים והעסקיים של הבקשה ברמה המקצועית הגבוהה ביותר.

## עקרונות כתיבה:
1. **שפה**: עברית אקדמית-תעשייתית. אובייקטיבית, מדויקת, ללא הגזמות שיווקיות.
2. **מבנה**: כל סעיף פותח בטענה מרכזית, מגובה בנתונים, ונחתם בהשלכה על הפרויקט.
3. **מיקוד**: הדגש את הצורך בשוק, הבידול הטכנולוגי, והפוטנציאל העסקי הגלובלי.
4. **קריטריונים**: התאם לקריטריוני הערכה של הרשות - חדשנות, שוק, צוות, היתכנות, תרומת המענק.

## מילות מפתח חיוניות (שלב אותן באופן טבעי):
- "הורדת סיכון טכנולוגי" (De-risking)
- "חופש פעולה" (Freedom to Operate)
- "יכולת הגנה" (Defensibility)
- "הוכחת היתכנות" (POC)
- "קפיצת מדרגה טכנולוגית"
- "תרומה לכלכלת ישראל"
- "פוטנציאל צמיחה גלובלי"

## הנחיות לסעיפים:
- **תקציר**: 150-200 מילים. מהות הפרויקט, החדשנות, והתוצר הצפוי.
- **צורך בשוק**: נתונים כמותיים (TAM/SAM), מגמות, כאבים ספציפיים.
- **ניתוח תחרותי**: השוואה מובנית (טבלה) מול 3-5 מתחרים, הדגשת הפער.
- **מודל עסקי**: מקורות הכנסה, מחירון צפוי, יעדי מכירות.
- **אסטרטגיית חדירה**: שוק יעד ראשוני, ערוצי הפצה, שותפויות.
- **צוות**: הדגשת ניסיון רלוונטי ויתרון תחרותי של הצוות.
- **תוצרים**: אבני דרך מדידות, ברורות וריאליסטיות ל-12 חודשים.
- **פוטנציאל צמיחה**: תרומה למשק (תעסוקה, ייצוא, IP ישראלי).
- **תוכנית מימון**: כיצד המענק מגשר לסבב גיוס הבא.

כתוב בעברית בלבד. אל תכלול כותרות סעיפים - רק את התוכן עצמו."""

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
                revision_notes = f"\n\nהערות לתיקון מסבב קודם:\n" + "\n".join(existing["revision_notes"])

            user_prompt = f"""כתוב את הסעיף: {section_def['title_he']}

הקשר על המיזם:
{context}
{revision_notes}

כתוב את התוכן לסעיף זה (400-800 מילים). עברית בלבד."""

            content = await self._generate(
                system_prompt=STRATEGIST_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=3000,
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
                sections = [new_section if s["section_id"] == section_id else s for s in sections]
            else:
                sections.append(new_section)

        # Also generate strategic summaries
        market_analysis = await self._generate_market_analysis(context)
        competitive = await self._generate_competitive_landscape(context)

        return {
            "sections": sections,
            "market_analysis_he": market_analysis,
            "competitive_landscape_he": competitive,
            "unfair_advantage_he": self._extract_unfair_advantage(state),
        }

    def _build_context(self, state: GrantState) -> str:
        parts = [f"שם המיזם: {state['startup_name']}"]
        parts.append(f"תיאור: {state['startup_description']}")

        if state.get("pitch_content"):
            parts.append(f"\nתוכן מצגת:\n{state['pitch_content'][:3000]}")

        if state.get("github_analysis"):
            ga = state["github_analysis"]
            parts.append(f"\nניתוח טכני: {ga.get('architecture_summary', '')}")
            if ga.get("languages"):
                parts.append(f"שפות תכנות: {', '.join(list(ga['languages'].keys())[:5])}")

        if state.get("team_profiles"):
            team_str = "\n".join(
                f"- {m['name']} ({m['role']}): {m['experience_summary']}"
                for m in state["team_profiles"]
            )
            parts.append(f"\nצוות:\n{team_str}")

        return "\n".join(parts)

    async def _generate_market_analysis(self, context: str) -> str:
        prompt = f"""בהתבסס על המידע הבא, כתוב ניתוח שוק תמציתי (200 מילים) הכולל:
- גודל שוק (TAM/SAM)
- מגמות צמיחה
- כאבים עיקריים של לקוחות היעד

{context}"""
        return await self._generate(STRATEGIST_SYSTEM_PROMPT, prompt, max_tokens=1000)

    async def _generate_competitive_landscape(self, context: str) -> str:
        prompt = f"""בהתבסס על המידע הבא, כתוב ניתוח תחרותי תמציתי (200 מילים) הכולל:
- פתרונות קיימים בשוק
- חולשות של המתחרים
- הבידול של המיזם שלנו

{context}"""
        return await self._generate(STRATEGIST_SYSTEM_PROMPT, prompt, max_tokens=1000)

    def _extract_unfair_advantage(self, state: GrantState) -> str:
        if state.get("github_analysis", {}).get("repositories"):
            repos = state["github_analysis"]["repositories"]
            patterns = set()
            for repo in repos:
                patterns.update(repo.get("patterns", []))
            if patterns:
                return f"יתרון טכנולוגי מוכח: {', '.join(patterns)}"
        return state.get("startup_description", "")[:200]
