# Tnufa (Ideation) Track - Innovation Authority Constants
# Based on procedure 200-02 and 2024-2025 updates

# === Financial Constants ===
MAX_BUDGET_NIS = 250_000
GRANT_RATE = 0.80
MAX_GRANT_NIS = 200_000  # min(0.8 * 250000, 200000)
SELF_FUNDING_RATE = 0.20

# Bio-Convergence track
BIO_MAX_BUDGET_NIS = 470_588
BIO_GRANT_RATE = 0.85
BIO_MAX_GRANT_NIS = 400_000

# Contractor limits
MAX_HOURLY_RATE_NIS = 300
EQUIPMENT_DEPRECIATION_RATE = 0.33  # 33% per year

# Duration
MAX_PROJECT_DURATION_MONTHS = 12

# Budget deviation allowed without pre-approval
BUDGET_DEVIATION_THRESHOLD = 0.15  # 15%

# Women entrepreneurs bonus
WOMEN_ENTREPRENEUR_BONUS = 0.10  # 10% additional grant

# === Eligible Expense Categories ===
ELIGIBLE_CATEGORIES = [
    "subcontractors",       # קבלני משנה
    "materials",            # חומרים ורכיבים
    "ip_patents",           # קניין רוחני
    "business_development", # פיתוח עסקי
    "equipment_depreciation",  # פחת ציוד
    "travel_abroad",        # נסיעות לחו"ל (תערוכות)
]

# === Forbidden Expenses ===
FORBIDDEN_EXPENSES = [
    "founder_salary",       # שכר יזמים
    "overhead",             # תקורה
    "rent",                 # שכר דירה
    "utilities",            # חשמל/מים
    "vat",                  # מע"מ
    "general_marketing",    # שיווק כללי (לא תערוכות)
]

# === Evaluation Criteria ===
EVALUATION_CRITERIA = {
    "innovation": {"weight": 0.30, "name_he": "חדשנות טכנולוגית"},
    "market": {"weight": 0.20, "name_he": "פוטנציאל עסקי גלובלי"},
    "team": {"weight": 0.20, "name_he": "יכולות הצוות"},
    "feasibility": {"weight": 0.15, "name_he": "היתכנות טכנו-כלכלית"},
    "grant_contribution": {"weight": 0.15, "name_he": "תרומת המענק לקידום"},
}

MINIMUM_PASSING_SCORE = 90

# === Eligibility Requirements ===
ELIGIBILITY_RULES = {
    "max_prior_funding_nis": 3_000_000,
    "entity_types": ["private_entrepreneur", "new_company"],
    "residency": "israel",
    "company_activity": "no_prior_commercial_activity",
}

# === Application Sections (Hebrew) ===
APPLICATION_SECTIONS = [
    {"id": "project_summary", "title_he": "תקציר הפרויקט", "agent": "strategist"},
    {"id": "market_need", "title_he": "הצורך והזדמנות השוק", "agent": "strategist"},
    {"id": "competitive_analysis", "title_he": "ניתוח תחרותי ומצב הידע הקיים", "agent": "strategist"},
    {"id": "innovation", "title_he": "החדשנות הטכנולוגית והבידול", "agent": "technical_writer"},
    {"id": "product_description", "title_he": "תיאור המוצר/שירות", "agent": "technical_writer"},
    {"id": "rd_plan", "title_he": "תוכנית מו\"פ ואבני דרך", "agent": "technical_writer"},
    {"id": "technical_challenges", "title_he": "אתגרים טכנולוגיים וסיכונים", "agent": "technical_writer"},
    {"id": "methodology", "title_he": "מתודולוגיה וגישת פיתוח", "agent": "technical_writer"},
    {"id": "ip_strategy", "title_he": "אסטרטגיית קניין רוחני", "agent": "technical_writer"},
    {"id": "current_state", "title_he": "מצב הפיתוח הנוכחי", "agent": "technical_writer"},
    {"id": "business_model", "title_he": "מודל עסקי", "agent": "strategist"},
    {"id": "go_to_market", "title_he": "אסטרטגיית חדירה לשוק", "agent": "strategist"},
    {"id": "team_capabilities", "title_he": "הצוות ויכולות המיזם", "agent": "strategist"},
    {"id": "budget_justification", "title_he": "נימוק התקציב", "agent": "cfo"},
    {"id": "work_plan", "title_he": "תוכנית עבודה רבעונית", "agent": "cfo"},
    {"id": "expected_outcomes", "title_he": "תוצרים צפויים ואבני דרך", "agent": "strategist"},
    {"id": "growth_potential", "title_he": "פוטנציאל צמיחה ותרומה לכלכלה", "agent": "strategist"},
    {"id": "funding_plan", "title_he": "תוכנית מימון והמשך גיוס", "agent": "cfo"},
]

# === Royalty Terms ===
ROYALTY_RATE = 0.03  # 3% of annual sales upon commercial success
