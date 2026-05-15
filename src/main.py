"""CLI entry point for the AI Grant Engine."""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("grant-engine")


def main():
    parser = argparse.ArgumentParser(
        description="AI Grant Engine - מנוע מענקים אוטומטי למסלול תנופה"
    )
    parser.add_argument("--name", required=True, help="Startup name")
    parser.add_argument("--description", required=True, help="Startup description")
    parser.add_argument("--github", nargs="*", default=[], help="GitHub repo URLs")
    parser.add_argument("--deck", nargs="*", default=[], help="Pitch deck file paths")
    parser.add_argument("--woman", action="store_true", help="Woman entrepreneur (10% bonus)")
    parser.add_argument("--entity", choices=["private_entrepreneur", "new_company"],
                       default="private_entrepreneur", help="Entity type")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--web", action="store_true", help="Launch Streamlit web UI")

    args = parser.parse_args()

    if args.web:
        _launch_web()
        return

    # Validate inputs
    if not args.name or not args.description:
        parser.error("--name and --description are required")

    # Load settings
    from dotenv import load_dotenv
    load_dotenv()

    from .config.settings import Settings
    settings = Settings()
    settings.output_dir = args.output

    available = settings.get_available_providers()
    if not available:
        logger.error("No LLM providers configured. Set at least one API key in .env")
        sys.exit(1)

    logger.info(f"Available providers: {', '.join(available.keys())}")
    logger.info(f"Starting grant application for: {args.name}")

    # Run pipeline
    asyncio.run(_run(args, settings))


async def _run(args, settings):
    from .graph.pipeline import compile_pipeline
    from .graph.state import create_initial_state

    state = create_initial_state(
        startup_name=args.name,
        startup_description=args.description,
        github_urls=args.github,
        uploaded_files=args.deck,
        is_woman_entrepreneur=args.woman,
        entity_type=args.entity,
    )

    pipeline = compile_pipeline()

    logger.info("=" * 60)
    logger.info("AI GRANT ENGINE - Starting Pipeline")
    logger.info("=" * 60)

    result = await pipeline.ainvoke(state)

    # Print results
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)

    if result.get("is_eligible") is False:
        logger.warning("❌ Project not eligible for Tnufa track")
        logger.warning(f"Notes: {result.get('eligibility_notes', [])}")
        return

    logger.info(f"✅ Score: {result.get('overall_score', 0):.1f}/100")
    logger.info(f"💰 Budget: ₪{result.get('total_budget', 0):,.0f}")
    logger.info(f"🎁 Grant: ₪{result.get('grant_amount', 0):,.0f}")
    logger.info(f"📄 Sections written: {len(result.get('sections', []))}")
    logger.info(f"🔄 Evaluation rounds: {result.get('evaluation_round', 0)}")
    logger.info(f"📁 Output: {settings.output_dir}")


def _launch_web():
    """Launch Streamlit web interface."""
    import subprocess
    web_path = Path(__file__).parent / "web" / "streamlit_app.py"
    subprocess.run(["streamlit", "run", str(web_path)], check=True)


if __name__ == "__main__":
    main()
