# AI Grant Engine - מנוע מענקים אוטומטי

מערכת רב-סוכנית (Multi-Agent) המבוססת על בינה מלאכותית לכתיבת בקשות מענק אוטומטיות למסלול **תנופה** (Ideation) של רשות החדשנות הישראלית.

## מה המערכת עושה?

- מקבלת חומרי גלם (GitHub repo, מצגת, קורות חיים)
- מייצרת בקשת מענק מלאה בעברית (Word + Excel)
- מוודאת עמידה בנוהל 200-02 ובקריטריוני הרשות
- ממקסמת את המענק (עד 200,000 ש"ח)

## ארכיטקטורה

```
Input → Ingestion → Eligibility → Strategist → Technical Writer → CFO → Red Team → Output
                                       ↑                              ↑        ↑       |
                                       └──── revision loop ──────────┘────────┘       |
                                                                    (score < 90)       ↓
                                                                              DOCX + XLSX
```

### 4 סוכנים:
1. **Strategist** - נרטיב עסקי, ניתוח שוק, מתחרים
2. **Technical Writer** - פרקי מו"פ ברמת דוקטורט
3. **CFO** - תקציב אופטימלי לפי נוהל 200-02
4. **Red Team** - מעריך ומחזיר לתיקון אם ציון < 90

### 7 ספקי LLM (חבר את מה שיש לך):
| ספק | סוג | מודל ברירת מחדל |
|-----|------|------------------|
| Groq | חינם | Llama 3.1 70B |
| Google Gemini | חינם | Gemini 1.5 Flash |
| Together AI | חינם | Llama 3.1 70B |
| OpenRouter | חינם/בתשלום | Llama 3.1 70B |
| Claude (Anthropic) | בתשלום | Claude Sonnet |
| OpenAI | בתשלום | GPT-4o |
| Mistral | בתשלום | Mistral Large |

## התקנה

```bash
# Clone
cd ai-grant-engine

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install
pip install -e .

# Configure
copy .env.example .env
# Edit .env and add at least one API key
```

## שימוש

### Web UI (מומלץ):
```bash
streamlit run src/web/streamlit_app.py
```

### CLI:
```bash
python -m src.main \
  --name "MyStartup" \
  --description "AI-powered solution for..." \
  --github https://github.com/user/repo \
  --deck pitch.pdf \
  --woman \
  --entity private_entrepreneur
```

## תקציב מסלול תנופה

| פרמטר | ערך |
|--------|------|
| תקציב מקסימלי | 250,000 ש"ח |
| שיעור מענק | 80% |
| מענק מקסימלי | 200,000 ש"ח |
| בונוס יזמות נשים | +10% |
| תקרת שעתי קבלנים | 300 ש"ח |
| משך פרויקט | 12 חודשים |

## מבנה הפרויקט

```
src/
├── config/          # Settings, constants (Tnufa rules)
├── llm/             # 7 LLM providers + smart router
├── agents/          # 4 specialized agents
├── graph/           # LangGraph pipeline + state
├── tools/           # GitHub analyzer, doc parser, budget calc
├── knowledge/       # ChromaDB RAG indexer
├── output/          # DOCX + XLSX generators
└── web/             # Streamlit UI
```

## בדיקות

```bash
python tests/test_budget_calculator.py
python tests/test_pipeline.py
# Or with pytest:
pytest tests/
```

## רישיון

MIT
