from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages


class ApplicationSection(TypedDict):
    section_id: str
    title_he: str
    content_he: str
    status: Literal["draft", "revised", "approved"]
    revision_notes: list[str]


class BudgetLine(TypedDict):
    category: str
    description_he: str
    amount: float
    grant_portion: float
    justification_he: str
    hourly_rate: float | None
    hours: float | None


class EvaluationScore(TypedDict):
    criterion: str
    score: int
    weight: float
    feedback_he: str
    suggestions: list[str]


class TeamMember(TypedDict):
    name: str
    role: str
    experience_summary: str
    linkedin_url: str


class GrantState(TypedDict):
    # === User Input ===
    startup_name: str
    startup_description: str
    github_urls: list[str]
    linkedin_urls: list[str]
    uploaded_files: list[str]
    is_woman_entrepreneur: bool
    entity_type: Literal["private_entrepreneur", "new_company"]

    # === Ingestion Results ===
    github_analysis: dict
    team_profiles: list[TeamMember]
    pitch_content: str
    raw_documents: list[dict]

    # === Eligibility ===
    is_eligible: bool
    eligibility_notes: list[str]

    # === Strategy (Strategist Agent) ===
    market_analysis_he: str
    competitive_landscape_he: str
    unfair_advantage_he: str
    business_model_he: str

    # === Application Sections ===
    sections: list[ApplicationSection]

    # === Financials (CFO Agent) ===
    budget_lines: list[BudgetLine]
    total_budget: float
    grant_amount: float
    self_funding: float
    budget_valid: bool
    budget_notes: list[str]

    # === Evaluation (Red Team) ===
    scores: list[EvaluationScore]
    overall_score: float
    evaluation_round: int
    max_rounds: int

    # === Pipeline Control ===
    current_stage: Literal[
        "ingestion",
        "matching",
        "drafting_strategy",
        "drafting_technical",
        "financials",
        "evaluation",
        "output",
        "complete",
        "rejected",
    ]
    revision_target: str | None
    error: str | None
    messages: Annotated[list, add_messages]


def create_initial_state(
    startup_name: str,
    startup_description: str,
    github_urls: list[str] | None = None,
    linkedin_urls: list[str] | None = None,
    uploaded_files: list[str] | None = None,
    is_woman_entrepreneur: bool = False,
    entity_type: str = "private_entrepreneur",
) -> GrantState:
    return GrantState(
        startup_name=startup_name,
        startup_description=startup_description,
        github_urls=github_urls or [],
        linkedin_urls=linkedin_urls or [],
        uploaded_files=uploaded_files or [],
        is_woman_entrepreneur=is_woman_entrepreneur,
        entity_type=entity_type,
        github_analysis={},
        team_profiles=[],
        pitch_content="",
        raw_documents=[],
        is_eligible=False,
        eligibility_notes=[],
        market_analysis_he="",
        competitive_landscape_he="",
        unfair_advantage_he="",
        business_model_he="",
        sections=[],
        budget_lines=[],
        total_budget=0.0,
        grant_amount=0.0,
        self_funding=0.0,
        budget_valid=False,
        budget_notes=[],
        scores=[],
        overall_score=0.0,
        evaluation_round=0,
        max_rounds=3,
        current_stage="ingestion",
        revision_target=None,
        error=None,
        messages=[],
    )
