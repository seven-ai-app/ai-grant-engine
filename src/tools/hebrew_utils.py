"""Hebrew language utilities for RTL document generation."""


def format_currency(amount: float) -> str:
    """Format number as Hebrew currency."""
    return f"{amount:,.0f} ש\"ח"


def format_percentage(value: float) -> str:
    """Format as percentage."""
    return f"{value * 100:.0f}%"


SECTION_HEADERS_HE = {
    "project_summary": "תקציר הפרויקט",
    "market_need": "הצורך והזדמנות השוק",
    "competitive_analysis": "ניתוח תחרותי ומצב הידע הקיים",
    "innovation": "החדשנות הטכנולוגית והבידול",
    "product_description": "תיאור המוצר/שירות",
    "rd_plan": "תוכנית מו\"פ ואבני דרך",
    "technical_challenges": "אתגרים טכנולוגיים וסיכונים",
    "methodology": "מתודולוגיה וגישת פיתוח",
    "ip_strategy": "אסטרטגיית קניין רוחני",
    "current_state": "מצב הפיתוח הנוכחי",
    "business_model": "מודל עסקי",
    "go_to_market": "אסטרטגיית חדירה לשוק",
    "team_capabilities": "הצוות ויכולות המיזם",
    "budget_justification": "נימוק התקציב",
    "work_plan": "תוכנית עבודה רבעונית",
    "expected_outcomes": "תוצרים צפויים ואבני דרך",
    "growth_potential": "פוטנציאל צמיחה ותרומה לכלכלה",
    "funding_plan": "תוכנית מימון והמשך גיוס",
}

BUDGET_CATEGORIES_HE = {
    "subcontractors": "קבלני משנה",
    "materials": "חומרים ורכיבים",
    "ip_patents": "קניין רוחני (פטנטים)",
    "business_development": "פיתוח עסקי",
    "equipment_depreciation": "פחת ציוד",
    "travel_abroad": "נסיעות לחו\"ל",
}

EVALUATION_CRITERIA_HE = {
    "innovation": "חדשנות טכנולוגית",
    "market": "פוטנציאל עסקי גלובלי",
    "team": "יכולות הצוות",
    "feasibility": "היתכנות טכנו-כלכלית",
    "grant_contribution": "תרומת המענק לקידום",
}
