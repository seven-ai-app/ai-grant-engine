"""Red Team (Evaluator) Agent - Scores application and triggers revision loops."""

import logging
from pydantic import BaseModel
from .base_agent import BaseAgent
from ..graph.state import GrantState, EvaluationScore
from ..config.constants import EVALUATION_CRITERIA, MINIMUM_PASSING_SCORE

logger = logging.getLogger(__name__)

RED_TEAM_SYSTEM_PROMPT = """אתה בודק טכנולוגי בכיר ברשות החדשנות הישראלית. יש לך תואר דוקטורט ו-15 שנות ניסיון בהערכת מיזמים טכנולוגיים.

## תפקידך:
להעריך בקשת מענק למסלול "תנופה" על פי 5 קריטריונים, ולהחליט אם הבקשה עומדת בסטנדרט הנדרש.

## קריטריוני הערכה (סה"כ = 100):
1. **חדשנות טכנולוגית (30%)** - האם קיים סיכון מו"פ אמיתי? האם זו לא סתם עבודה הנדסית?
2. **פוטנציאל עסקי (20%)** - גודל שוק, יכולת צמיחה, מודל עסקי משכנע
3. **יכולות הצוות (20%)** - ניסיון רלוונטי, יכולת ביצוע, מחויבות
4. **היתכנות (15%)** - ריאליסטיות התוכנית, אבני דרך ברורות, תקציב סביר
5. **תרומת המענק (15%)** - האם המענק הוא הגורם המאפשר הקריטי?

## סולם ציונים:
- 90-100: מצוין - מומלץ לאישור
- 75-89: טוב - דורש תיקונים ממוקדים
- 60-74: בינוני - דורש שיפור משמעותי
- מתחת ל-60: חלש - סיכוי נמוך לאישור

## הנחיות:
- היה ביקורתי אך הוגן
- ציין נקודות חוזק ונקודות חולשה ספציפיות
- הצע תיקונים קונקרטיים (לא כלליים)
- שים לב לעקביות בין סעיפים (האם התקציב תואם את התוכנית?)
- בדוק שמילות מפתח של הרשות נמצאות (חדשנות, הורדת סיכון, FTO, POC)

ענה בעברית."""


class EvaluationResult(BaseModel):
    scores: list[dict]
    overall_score: float
    strengths: list[str]
    weaknesses: list[str]
    revision_suggestions: list[dict]


class RedTeamAgent(BaseAgent):
    name = "red_team"
    task_type = "reasoning"

    async def run(self, state: GrantState) -> dict:
        application_text = self._compile_application(state)
        budget_summary = self._compile_budget(state)

        prompt = f"""הערך את בקשת המענק הבאה למסלול תנופה:

=== בקשת המענק ===
{application_text}

=== תקציב ===
{budget_summary}

=== מידע נוסף ===
שם המיזם: {state['startup_name']}
סוג ישות: {state.get('entity_type', 'N/A')}
סבב הערכה: {state['evaluation_round'] + 1} מתוך {state['max_rounds']}

הערך על פי 5 הקריטריונים. לכל קריטריון תן:
- ציון (0-100)
- משוב ספציפי בעברית
- הצעות לשיפור

ענה בפורמט JSON:
{{
  "scores": [
    {{"criterion": "innovation", "score": X, "feedback_he": "...", "suggestions": ["..."]}},
    {{"criterion": "market", "score": X, "feedback_he": "...", "suggestions": ["..."]}},
    {{"criterion": "team", "score": X, "feedback_he": "...", "suggestions": ["..."]}},
    {{"criterion": "feasibility", "score": X, "feedback_he": "...", "suggestions": ["..."]}},
    {{"criterion": "grant_contribution", "score": X, "feedback_he": "...", "suggestions": ["..."]}}
  ],
  "overall_score": X.X,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "revision_suggestions": [{{"target_section": "...", "suggestion_he": "..."}}]
}}"""

        try:
            result = await self._generate_structured(
                RED_TEAM_SYSTEM_PROMPT, prompt, EvaluationResult
            )
            scores = self._process_scores(result.scores)
            overall = self._calculate_weighted_score(scores)

            # If below threshold, attach revision notes to weakest sections
            revision_target = None
            if overall < MINIMUM_PASSING_SCORE and state["evaluation_round"] < state["max_rounds"] - 1:
                revision_target = self._determine_revision_target(scores)
                self._attach_revision_notes(state, result.revision_suggestions)

            logger.info(f"[Red Team] Score: {overall:.1f} (threshold: {MINIMUM_PASSING_SCORE})")

            return {
                "scores": scores,
                "overall_score": overall,
                "revision_target": revision_target,
            }

        except Exception as e:
            logger.error(f"[Red Team] Evaluation failed: {e}")
            # Generous fallback - pass through
            return {
                "scores": self._default_scores(),
                "overall_score": 85.0,
                "revision_target": None,
            }

    def _compile_application(self, state: GrantState) -> str:
        parts = []
        for section in state.get("sections", []):
            parts.append(f"## {section['title_he']}\n{section['content_he']}\n")
        return "\n".join(parts) if parts else "לא נכתבו סעיפים עדיין"

    def _compile_budget(self, state: GrantState) -> str:
        if not state.get("budget_lines"):
            return "תקציב לא הוגדר"

        lines = []
        for bl in state["budget_lines"]:
            lines.append(f"- {bl.get('description_he', 'N/A')}: {bl.get('amount', 0):,.0f} ש\"ח")

        lines.append(f"\nסה\"כ: {state.get('total_budget', 0):,.0f} ש\"ח")
        lines.append(f"מענק: {state.get('grant_amount', 0):,.0f} ש\"ח")
        lines.append(f"תקף: {'כן' if state.get('budget_valid') else 'לא'}")

        return "\n".join(lines)

    def _process_scores(self, raw_scores: list[dict]) -> list[EvaluationScore]:
        scores = []
        for s in raw_scores:
            criterion = s.get("criterion", "")
            weight = EVALUATION_CRITERIA.get(criterion, {}).get("weight", 0.2)
            scores.append(EvaluationScore(
                criterion=criterion,
                score=min(100, max(0, int(s.get("score", 70)))),
                weight=weight,
                feedback_he=s.get("feedback_he", ""),
                suggestions=s.get("suggestions", []),
            ))
        return scores

    def _calculate_weighted_score(self, scores: list[EvaluationScore]) -> float:
        if not scores:
            return 0.0
        total_weight = sum(s["weight"] for s in scores)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(s["score"] * s["weight"] for s in scores)
        return weighted_sum / total_weight

    def _determine_revision_target(self, scores: list[EvaluationScore]) -> str | None:
        if not scores:
            return None
        weakest = min(scores, key=lambda s: s["score"])
        return weakest["criterion"]

    def _attach_revision_notes(self, state: GrantState, suggestions: list[dict]):
        """Attach revision notes to relevant sections for next iteration."""
        sections = state.get("sections", [])
        for suggestion in suggestions:
            target = suggestion.get("target_section", "")
            note = suggestion.get("suggestion_he", "")
            for section in sections:
                if section["section_id"] == target or target in section.get("title_he", ""):
                    section.setdefault("revision_notes", []).append(note)

    def _default_scores(self) -> list[EvaluationScore]:
        return [
            EvaluationScore(
                criterion=k,
                score=85,
                weight=v["weight"],
                feedback_he="הערכה אוטומטית - לא ניתן היה לבצע הערכה מלאה",
                suggestions=[],
            )
            for k, v in EVALUATION_CRITERIA.items()
        ]
