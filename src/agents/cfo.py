"""CFO Agent - Budget optimization per Innovation Authority procedure 200-02."""

import logging
from pydantic import BaseModel
from .base_agent import BaseAgent
from ..graph.state import GrantState, ApplicationSection, BudgetLine
from ..tools.budget_calculator import calculate_grant, validate_budget, optimize_budget
from ..config.constants import (
    MAX_BUDGET_NIS,
    MAX_GRANT_NIS,
    GRANT_RATE,
    MAX_HOURLY_RATE_NIS,
    APPLICATION_SECTIONS,
    ELIGIBLE_CATEGORIES,
)

logger = logging.getLogger(__name__)

CFO_SYSTEM_PROMPT = """אתה מנהל כספים (CFO) מומחה בתקציבי מו"פ ומענקי רשות החדשנות הישראלית.

## מומחיות:
- נוהל 200-02 של הרשות לחדשנות
- מסלול תנופה (Ideation): תקציב מקסימלי 250,000 ש"ח, מענק עד 80% (200,000 ש"ח)
- הוצאות מוכרות ואסורות
- אופטימיזציה של תקציב למקסום מענק

## כללים קשיחים (אסור לחרוג):
1. תקרת תעריף שעתי לקבלני משנה: 300 ש"ח/שעה
2. אסור: שכר יזמים, תקורה, שכ"ד, חשמל, מע"מ
3. מותר: קבלני משנה, חומרים, פטנטים, פיתוח עסקי, פחת ציוד (33%/שנה)
4. סטייה מותרת בין סעיפים: עד 15% ללא אישור מראש
5. נסיעות לחו"ל: רק לתערוכות מקצועיות, מוגבל

## אסטרטגיית תקצוב:
- מקסם את התקציב הכולל ל-250,000 ש"ח (מענק מקסימלי: 200,000 ש"ח)
- וודא שכל שורת תקציב מנומקת וקשורה למשימת מו"פ ספציפית
- בנה חיץ של 5-10% לחריגות בלתי צפויות
- הפרד בין רבעונים בתוכנית העבודה

כתוב בעברית. היה מדויק במספרים."""

CFO_SECTIONS = [s for s in APPLICATION_SECTIONS if s["agent"] == "cfo"]


class BudgetProposal(BaseModel):
    lines: list[dict]
    total: float
    reasoning: str


class CFOAgent(BaseAgent):
    name = "cfo"
    task_type = "structured"

    async def run(self, state: GrantState) -> dict:
        # Generate budget based on project needs
        budget_lines = await self._generate_budget(state)

        # Validate against rules
        validation = validate_budget(
            budget_lines,
            is_woman_entrepreneur=state.get("is_woman_entrepreneur", False),
        )

        # If invalid, fix issues
        if not validation.is_valid:
            logger.warning(f"[CFO] Budget validation errors: {validation.errors}")
            budget_lines = self._fix_budget_errors(budget_lines, validation.errors)
            validation = validate_budget(
                budget_lines,
                is_woman_entrepreneur=state.get("is_woman_entrepreneur", False),
            )

        # Generate budget-related application sections
        sections = list(state.get("sections", []))
        sections = await self._generate_budget_sections(state, sections, budget_lines, validation)

        return {
            "sections": sections,
            "budget_lines": budget_lines,
            "total_budget": validation.total_budget,
            "grant_amount": validation.grant_amount,
            "self_funding": validation.self_funding,
            "budget_valid": validation.is_valid,
            "budget_notes": validation.errors + validation.warnings,
        }

    async def _generate_budget(self, state: GrantState) -> list[BudgetLine]:
        context = self._build_context(state)

        prompt = f"""בהתבסס על המיזם הבא, בנה תקציב מפורט למסלול תנופה.

{context}

## חובות תקציב (אסור להחמיץ):
1. חובה לכלול שורת קניין רוחני (ip_patents): סקר פטנטים (FTO) + פטנט זמני - 15,000-20,000 ש"ח
2. תקציב כולל חייב להיות בין 240,000-250,000 ש"ח (מקסום מענק!)
3. כל שורת קבלן משנה: ציין שם/תחום, שעות × תעריף (עד 300 ש"ח/שעה)

## קטגוריות מותרות:
- subcontractors (קבלני משנה - עד 300 ש"ח/שעה) - עיקר התקציב
- materials (חומרים, שרתי ענן, רכיבים)
- ip_patents (קניין רוחני - חובה!)
- business_development (פיתוח עסקי, יועץ שיווק)
- equipment_depreciation (פחת ציוד - 33%/שנה בלבד)
- travel_abroad (נסיעות - תערוכות מקצועיות בלבד)

## אסור לכלול:
- שכר יזמים/מייסדים
- שכ"ד, חשמל, תקורה כללית
- מע"מ

עבור כל שורה ספק: category, description_he, amount, justification_he, hourly_rate (אם רלוונטי), hours (אם רלוונטי).
ענה בפורמט JSON: {{"lines": [...], "total": number, "reasoning": "..."}}"""

        try:
            result = await self._generate_structured(
                CFO_SYSTEM_PROMPT, prompt, BudgetProposal
            )
            return self._convert_to_budget_lines(result.lines)
        except Exception as e:
            logger.warning(f"Structured generation failed, using fallback: {e}")
            return self._generate_default_budget(state)

    def _convert_to_budget_lines(self, lines: list[dict]) -> list[BudgetLine]:
        budget_lines = []
        for line in lines:
            amount = float(line.get("amount", 0))
            hourly_rate = line.get("hourly_rate")
            if hourly_rate:
                hourly_rate = min(float(hourly_rate), MAX_HOURLY_RATE_NIS)

            budget_lines.append(BudgetLine(
                category=line.get("category", "subcontractors"),
                description_he=line.get("description_he", ""),
                amount=amount,
                grant_portion=amount * GRANT_RATE,
                justification_he=line.get("justification_he", ""),
                hourly_rate=hourly_rate,
                hours=line.get("hours"),
            ))
        return budget_lines

    def _generate_default_budget(self, state: GrantState) -> list[BudgetLine]:
        """Fallback budget when LLM structured generation fails. Targets 250,000 NIS."""
        return [
            BudgetLine(
                category="subcontractors",
                description_he="מפתח בכיר - ארכיטקטורה וליבת המערכת",
                amount=84_000,
                grant_portion=67_200,
                justification_he="מפתח בכיר Full-Stack לפיתוח ארכיטקטורת הליבה: 280 שעות × 300 ₪/שעה. כולל עיצוב מסד הנתונים, API, תשתית Cloud.",
                hourly_rate=300,
                hours=280,
            ),
            BudgetLine(
                category="subcontractors",
                description_he="חוקר AI/ML - פיתוח אלגוריתמים ומודלים",
                amount=66_000,
                grant_portion=52_800,
                justification_he="חוקר ML מומחה לפיתוח אלגוריתם הליבה ואימון מודלים: 220 שעות × 300 ₪/שעה. כולל ניסויים, Hyperparameter Tuning, אופטימיזציה.",
                hourly_rate=300,
                hours=220,
            ),
            BudgetLine(
                category="subcontractors",
                description_he="מעצב UX/UI ו-Product Designer",
                amount=30_000,
                grant_portion=24_000,
                justification_he="מעצב בכיר לפיתוח ממשק המשתמש ו-User Journey: 150 שעות × 200 ₪/שעה. כולל Wireframes, Prototype, Usability Testing.",
                hourly_rate=200,
                hours=150,
            ),
            BudgetLine(
                category="subcontractors",
                description_he="בודק QA ומהנדס DevOps",
                amount=22_500,
                grant_portion=18_000,
                justification_he="מהנדס QA לבדיקות מערכת ו-DevOps לתשתיות CI/CD: 150 שעות × 150 ₪/שעה. כולל Load Testing, Security Testing.",
                hourly_rate=150,
                hours=150,
            ),
            BudgetLine(
                category="materials",
                description_he="תשתיות ענן ומחשוב לפיתוח ובדיקות",
                amount=18_000,
                grant_portion=14_400,
                justification_he="AWS/GCP: שרתי GPU לאימון מודלים, שרתי API, אחסון Dataset, CDN. 18,000 ₪ ל-12 חודשי פיתוח.",
                hourly_rate=None,
                hours=None,
            ),
            BudgetLine(
                category="ip_patents",
                description_he="סקר פטנטים (Freedom to Operate) ופטנט זמני",
                amount=18_000,
                grant_portion=14_400,
                justification_he="סקר FTO ע\"י עו\"ד פטנטים: 10,000 ₪. פטנט זמני (Provisional) בארה\"ב לחידושי הליבה: 8,000 ₪. חיוני להגנה טרם כניסה לשוק.",
                hourly_rate=None,
                hours=None,
            ),
            BudgetLine(
                category="business_development",
                description_he="יועץ עסקי ופיתוח שוק",
                amount=7_500,
                grant_portion=6_000,
                justification_he="יועץ Business Development לתיקוף שוק, גיוס לקוחות פיילוט ובניית Go-to-Market: 50 שעות × 150 ₪/שעה.",
                hourly_rate=150,
                hours=50,
            ),
            BudgetLine(
                category="travel_abroad",
                description_he="השתתפות בכנס/תערוכה בינלאומית מקצועית",
                amount=4_000,
                grant_portion=3_200,
                justification_he="השתתפות בתערוכה מקצועית בינלאומית בתחום (כגון CES / Web Summit / TechCrunch Disrupt): טיסה + לינה + כרטיס כניסה.",
                hourly_rate=None,
                hours=None,
            ),
        ]

    def _fix_budget_errors(self, lines: list[BudgetLine], errors: list[str]) -> list[BudgetLine]:
        """Fix common budget errors."""
        fixed = []
        for line in lines:
            # Fix hourly rate cap
            if line.get("hourly_rate") and line["hourly_rate"] > MAX_HOURLY_RATE_NIS:
                line = dict(line)
                line["hourly_rate"] = MAX_HOURLY_RATE_NIS
                if line.get("hours"):
                    line["amount"] = line["hourly_rate"] * line["hours"]
                    line["grant_portion"] = line["amount"] * GRANT_RATE

            # Skip forbidden categories
            if line.get("category") in ["founder_salary", "overhead", "rent", "utilities", "vat"]:
                continue

            fixed.append(line)

        # Scale to target if over budget
        total = sum(l.get("amount", 0) for l in fixed)
        if total > MAX_BUDGET_NIS:
            scale = MAX_BUDGET_NIS / total
            for line in fixed:
                line = dict(line)
                line["amount"] = round(line["amount"] * scale, -2)
                line["grant_portion"] = line["amount"] * GRANT_RATE

        return fixed

    async def _generate_budget_sections(
        self, state: GrantState, sections: list, budget_lines: list, validation
    ) -> list:
        """Generate budget justification and work plan sections."""
        budget_summary = self._format_budget_summary(budget_lines, validation)

        for section_def in CFO_SECTIONS:
            section_id = section_def["id"]
            existing = next((s for s in sections if s["section_id"] == section_id), None)

            if existing and existing["status"] == "approved":
                continue

            prompt = f"""כתוב את הסעיף: {section_def['title_he']}

פירוט תקציב:
{budget_summary}

שם המיזם: {state['startup_name']}
תיאור: {state['startup_description']}

כתוב נימוק מקצועי (300-500 מילים) המסביר את הקצאת המשאבים. עברית בלבד."""

            content = await self._generate(
                CFO_SYSTEM_PROMPT, prompt, temperature=0.5, max_tokens=2000
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

        return sections

    def _format_budget_summary(self, budget_lines: list, validation) -> str:
        lines = []
        for bl in budget_lines:
            rate_str = f" ({bl.get('hourly_rate', 0)} ש\"ח/שעה)" if bl.get("hourly_rate") else ""
            lines.append(f"- {bl.get('description_he', '')}: {bl.get('amount', 0):,.0f} ש\"ח{rate_str}")

        lines.append(f"\nסה\"כ תקציב: {validation.total_budget:,.0f} ש\"ח")
        lines.append(f"מענק מבוקש: {validation.grant_amount:,.0f} ש\"ח")
        lines.append(f"מימון עצמי: {validation.self_funding:,.0f} ש\"ח")

        return "\n".join(lines)

    def _build_context(self, state: GrantState) -> str:
        parts = [
            f"שם המיזם: {state['startup_name']}",
            f"תיאור: {state['startup_description']}",
        ]
        if state.get("github_analysis", {}).get("architecture_summary"):
            parts.append(f"טכנולוגיה: {state['github_analysis']['architecture_summary']}")
        return "\n".join(parts)
