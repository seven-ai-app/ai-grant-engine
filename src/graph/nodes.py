import logging
from .state import GrantState

logger = logging.getLogger(__name__)


async def ingest_node(state: GrantState) -> dict:
    """Scan GitHub repos, parse uploaded documents, extract team info."""
    from ..tools.github_analyzer import analyze_github_repos
    from ..tools.document_parser import parse_uploaded_files

    logger.info(f"[Ingestion] Processing inputs for: {state['startup_name']}")

    github_analysis = {}
    if state["github_urls"]:
        github_analysis = await analyze_github_repos(state["github_urls"])

    raw_documents = []
    pitch_content = ""
    if state["uploaded_files"]:
        raw_documents = await parse_uploaded_files(state["uploaded_files"])
        pitch_content = "\n\n".join(doc.get("content", "") for doc in raw_documents)

    return {
        "github_analysis": github_analysis,
        "raw_documents": raw_documents,
        "pitch_content": pitch_content,
        "current_stage": "matching",
    }


async def eligibility_node(state: GrantState) -> dict:
    """Check if startup meets Tnufa eligibility requirements."""
    from ..tools.rag_retriever import check_eligibility

    logger.info("[Matching] Checking eligibility against Tnufa requirements")

    is_eligible, notes = await check_eligibility(
        entity_type=state["entity_type"],
        startup_description=state["startup_description"],
        github_analysis=state["github_analysis"],
    )

    return {
        "is_eligible": is_eligible,
        "eligibility_notes": notes,
        "current_stage": "drafting_strategy" if is_eligible else "rejected",
    }


async def strategist_node(state: GrantState) -> dict:
    """Generate strategic narrative sections of the application."""
    from ..agents.strategist import StrategistAgent
    from ..config.settings import Settings
    from ..llm.router import LLMRouter

    logger.info("[Strategist] Drafting market & strategy sections")

    settings = Settings()
    router = LLMRouter(settings)
    agent = StrategistAgent(router)

    result = await agent.run(state)
    return {
        **result,
        "current_stage": "drafting_technical",
    }


async def technical_writer_node(state: GrantState) -> dict:
    """Generate technical/R&D sections from GitHub analysis."""
    from ..agents.technical_writer import TechnicalWriterAgent
    from ..config.settings import Settings
    from ..llm.router import LLMRouter

    logger.info("[Technical Writer] Drafting R&D sections")

    settings = Settings()
    router = LLMRouter(settings)
    agent = TechnicalWriterAgent(router)

    result = await agent.run(state)
    return {
        **result,
        "current_stage": "financials",
    }


async def cfo_node(state: GrantState) -> dict:
    """Build optimized budget within Tnufa constraints."""
    from ..agents.cfo import CFOAgent
    from ..config.settings import Settings
    from ..llm.router import LLMRouter

    logger.info("[CFO] Building budget")

    settings = Settings()
    router = LLMRouter(settings)
    agent = CFOAgent(router)

    result = await agent.run(state)
    return {
        **result,
        "current_stage": "evaluation",
    }


async def red_team_node(state: GrantState) -> dict:
    """Evaluate application quality and decide if revision needed."""
    from ..agents.red_team import RedTeamAgent
    from ..config.settings import Settings
    from ..llm.router import LLMRouter

    logger.info(f"[Red Team] Evaluation round {state['evaluation_round'] + 1}")

    settings = Settings()
    router = LLMRouter(settings)
    agent = RedTeamAgent(router)

    result = await agent.run(state)
    return {
        **result,
        "evaluation_round": state["evaluation_round"] + 1,
    }


async def output_node(state: GrantState) -> dict:
    """Generate final DOCX and XLSX files."""
    from ..output.docx_generator import generate_application_docx
    from ..output.xlsx_generator import generate_budget_xlsx
    from ..config.settings import Settings

    logger.info("[Output] Generating final documents")

    settings = Settings()
    output_dir = settings.output_path

    docx_path = generate_application_docx(state, output_dir)
    xlsx_path = generate_budget_xlsx(state, output_dir)

    logger.info(f"[Output] Generated: {docx_path}, {xlsx_path}")

    return {
        "current_stage": "complete",
    }
