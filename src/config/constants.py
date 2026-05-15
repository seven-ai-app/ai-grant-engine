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
    {"id": "executive_summary", "title_he": "סיכום מנהלים",
     "agent": "strategist", "max_words": 300,
     "instructions_he": "עד 15 שורות. [1] הצורך, המוצר, הטכנולוגיה, החדשנות, עיקרי תכולת הפיתוח, יעדים שיושגו בעזרת המענק. [2] השוק הרלוונטי, תיקוף שוק, מתחרים, ההזדמנות העסקית, המודל העסקי, תוכנית גיוס הון."},
    {"id": "the_need", "title_he": "הצורך",
     "agent": "strategist", "max_words": 500,
     "instructions_he": "תאר ופרט: מהי הבעיה שהמיזם פותר. כלול נתונים כמותיים, מקורות, מחקרים. הסבר מדוע הפתרונות הקיימים לא מספקים. הצג כאב השוק בצורה משכנעת."},
    {"id": "the_product", "title_he": "המוצר",
     "agent": "technical_writer", "max_words": 600,
     "instructions_he": "תאר: [1] המוצר והאופן בו הוא עונה לצורך. [2] מרכיבי המוצר, רכיביו ועקרונות הפעולה שלו. [3] תרחישי שימוש (use cases) מפורטים."},
    {"id": "team_capabilities", "title_he": "הצוות ויכולות המיזם",
     "agent": "strategist", "max_words": 600,
     "instructions_he": "תאר: [1] הרקע והניסיון הרלוונטי של כל אחד מאנשי המפתח. [2] יכולות הצוות לממש את המיזם. [3] קבלני משנה מהותיים. [4] יועצים ומלווים. [5] משקיעים ושותפים אסטרטגיים."},
    {"id": "capability_gaps", "title_he": "פערים ביכולות המיזם",
     "agent": "strategist", "max_words": 300,
     "instructions_he": "תאר: [1] הפערים בין היכולות הקיימות לנדרשות. [2] כיצד המענק יגשר על פערים אלו (קבלני משנה, רכישת ידע, שת\"פ, יועצים)."},
    {"id": "ip_rights", "title_he": "קניין רוחני - הפרת זכויות וסקירת פטנטים",
     "agent": "technical_writer", "max_words": 400,
     "instructions_he": "תאר: [1] האם נבדק שהפיתוח אינו מפר זכויות קניין של אחרים - אופן הבדיקה. [2] זכויות קניין בידע המקדמי. [3] שימוש ברכיבי צד ג' - פטנטים, רישיונות שימוש."},
    {"id": "ip_ownership", "title_he": "הבעלות במוצרי המיזם",
     "agent": "technical_writer", "max_words": 300,
     "instructions_he": "תאר: [1] כל זכויות הקניין בטכנולוגיות ומוצרי המיזם הנם בבעלות בלעדית של המגיש. [2] ידע חדש שייווצר - מי הבעלים. [3] זכויות קבלני משנה."},
    {"id": "development_status", "title_he": "סטטוס הפיתוח במועד ההגשה",
     "agent": "technical_writer", "max_words": 400,
     "instructions_he": "תאר: [1] הטכנולוגיות והמוצרים הקיימים כבר במיזם. [2] יעדים ומטרות שהושגו עד כה. [3] TRL (רמת בשלות טכנולוגית). מה כבר בנוי, אבני דרך שהושגו."},
    {"id": "technology", "title_he": "הטכנולוגיה",
     "agent": "technical_writer", "max_words": 700,
     "instructions_he": "תאר: [1] הטכנולוגיות שיפותחו בפרויקט זה. [2] מפרט ביצועים כמותי, תרשים זרימה, סכמת בלוקים. [3] ביסוס והתכנות. [4] חסמי כניסה טכנולוגיים. כלול אלגוריתמים ספציפיים, ארכיטקטורה, שפות תכנות."},
    {"id": "innovation_uniqueness", "title_he": "ייחודיות וחדשנות",
     "agent": "technical_writer", "max_words": 500,
     "instructions_he": "תאר: [1] החדשנות הטכנולוגית ביחס לטכנולוגיות אחרות בשוק. [2] החדשנות הפונקציונלית ביחס למוצרים קיימים. מה לא קיים היום שאתה בונה, מה ה-breakthrough."},
    {"id": "challenges_solutions", "title_he": "אתגרים ופתרונות",
     "agent": "technical_writer", "max_words": 400,
     "instructions_he": "תאר: [1] האתגרים הטכנולוגיים/מדעיים המרכזיים הצפויים בפיתוח. [2] אופן ההתמודדות עם כל אתגר. [3] סיכוני הפיתוח ומיטיגציה."},
    {"id": "rd_tasks", "title_he": "משימות המו\"פ בבקשה זו",
     "agent": "technical_writer", "max_words": 700,
     "instructions_he": "פרט 5-7 משימות מו\"פ. לכל משימה: שם, תיאור מפורט (3-5 שלבים), מועד התחלה וסיום. דוגמה: 'פיתוח אלגוריתם ליבה': 1. אפיון דרישות 2. מחקר ספרות 3. קידוד 4. בדיקות. כסה: מחקר בסיסי, פיתוח אלגוריתמים, בניית POC, שילוב מערכות, בדיקות."},
    {"id": "other_activities", "title_he": "פעילויות אחרות (שאינן מו\"פ)",
     "agent": "strategist", "max_words": 300,
     "instructions_he": "פרט פעילויות שאינן מו\"פ: הכנת תוכנית עסקית, רישום פטנט, תיקוף שוק עם לקוחות פוטנציאלים, גיוס מנהל שיווק, הגשת בקשת פטנט."},
    {"id": "market_segments", "title_he": "שוק - פלחי השוק הרלוונטיים",
     "agent": "strategist", "max_words": 500,
     "instructions_he": "תאר (עם מקורות): [1] פלח השוק הרלוונטי. [2] TAM/SAM/SOM - גדלים ותחזיות. [3] קצב גידול שנתי (CAGR). [4] מגמות עיקריות. [5] נתח שוק חזוי. השתמש בנתונים ממחקרי שוק - Gartner, IDC, Statista."},
    {"id": "customers", "title_he": "לקוחות",
     "agent": "strategist", "max_words": 400,
     "instructions_he": "תאר: [1] אפיון מפורט של לקוחות ישירים ולקוחות קצה. [2] ICP (ideal customer profile) - גודל ארגון, ענף, בעיה ספציפית. [3] מי משלם ומי משתמש."},
    {"id": "market_validation", "title_he": "תיקוף שוק ושותפויות",
     "agent": "strategist", "max_words": 400,
     "instructions_he": "תאר: [1] פגישות שהתבצעו עם לקוחות פוטנציאלים לתיקוף הצורך. [2] המשוב שהתקבל. [3] מוכנות לשלם. [4] שיתופי פעולה קיימים או בהתהוות. אם אין עדיין - תוכנית לתיקוף שוק במסגרת תנופה."},
    {"id": "business_model", "title_he": "מודל עסקי",
     "agent": "strategist", "max_words": 400,
     "instructions_he": "תאר: [1] מודל הכנסות (SaaS, רישיון, עמלה, חד-פעמי). [2] מחירון משוער. [3] ערוצי שיווק. [4] שותפויות. [5] תחזית הכנסות שנים 1-3."},
    {"id": "competition", "title_he": "תחרות - מוצרים מתחרים ויתרון תחרותי",
     "agent": "strategist", "max_words": 700,
     "instructions_he": "תאר: [1] קטגוריית המוצר. [2] גישות קיימות לצורך. [3] יתרונות תחרותיים. [4] ציין לפחות 4-6 מתחרים ספציפיים עם: שם חברה, כתובת אתר, מאפיינים, מחיר, נתח שוק, חולשות. [5] הסבר מדוע הלקוח יעדיף אותנו."},
    {"id": "market_barriers", "title_he": "חסמי כניסה לשוק",
     "agent": "strategist", "max_words": 300,
     "instructions_he": "תאר: [1] חסמי כניסה (רישוי, תקינה, רגולציה, הסמכות כמו FDA/CE/ISO). [2] כיצד המיזם יתמודד עם חסמים אלו."},
    {"id": "grant_contribution", "title_he": "תרומת מענק תנופה להצלחת המיזם",
     "agent": "strategist", "max_words": 400,
     "instructions_he": "הסבר: [1] כיצד המענק מאפשר להגיע לאבן דרך משמעותית. [2] אסטרטגיית גיוס מימון - מה יקרה אחרי תנופה (seed round, לקוחות משלמים). [3] מדוע ללא המענק הפיתוח לא יקרה - הוכח שהמענק הוא תנאי הכרחי."},
    {"id": "israeli_economy", "title_he": "התרומה הטכנולוגית והתעסוקתית לכלכלה הישראלית",
     "agent": "strategist", "max_words": 300,
     "instructions_he": "תאר: תרומה לתעסוקה (כמה עובדים שנה 1-3), ייצוא, IP ישראלי, חדשנות, אם יש פעילות בפריפריה. ציין אם יש יזם מאוכלוסיות תת-מיוצגות."},
]

# === Royalty Terms ===
ROYALTY_RATE = 0.03  # 3% of annual sales upon commercial success
