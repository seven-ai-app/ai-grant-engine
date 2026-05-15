"""Tests for the LangGraph pipeline structure."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.state import create_initial_state, GrantState
from src.graph.edges import route_eligibility, route_after_evaluation
from src.config.constants import EVALUATION_CRITERIA, MINIMUM_PASSING_SCORE


def test_create_initial_state():
    """Initial state should have all required fields."""
    state = create_initial_state(
        startup_name="TestCo",
        startup_description="A test startup",
        github_urls=["https://github.com/test/repo"],
    )
    assert state["startup_name"] == "TestCo"
    assert state["current_stage"] == "ingestion"
    assert state["evaluation_round"] == 0
    assert state["max_rounds"] == 3
    assert state["is_eligible"] is False


def test_route_eligibility_pass():
    """Eligible startup should route to strategist."""
    state = create_initial_state("X", "Y")
    state["is_eligible"] = True
    assert route_eligibility(state) == "eligible"


def test_route_eligibility_fail():
    """Non-eligible startup should route to end."""
    state = create_initial_state("X", "Y")
    state["is_eligible"] = False
    assert route_eligibility(state) == "not_eligible"


def test_route_after_evaluation_approved():
    """Score >= 90 should route to output."""
    state = create_initial_state("X", "Y")
    state["overall_score"] = 92.0
    state["evaluation_round"] = 1
    state["scores"] = [
        {"criterion": "innovation", "score": 95, "weight": 0.3, "feedback_he": "", "suggestions": []},
    ]
    assert route_after_evaluation(state) == "approved"


def test_route_after_evaluation_revise_technical():
    """Low innovation score should route to technical writer."""
    state = create_initial_state("X", "Y")
    state["overall_score"] = 75.0
    state["evaluation_round"] = 1
    state["max_rounds"] = 3
    state["scores"] = [
        {"criterion": "innovation", "score": 60, "weight": 0.3, "feedback_he": "", "suggestions": []},
        {"criterion": "market", "score": 85, "weight": 0.2, "feedback_he": "", "suggestions": []},
        {"criterion": "team", "score": 80, "weight": 0.2, "feedback_he": "", "suggestions": []},
    ]
    assert route_after_evaluation(state) == "revise_technical"


def test_route_after_evaluation_revise_strategy():
    """Low market/team score should route to strategist."""
    state = create_initial_state("X", "Y")
    state["overall_score"] = 72.0
    state["evaluation_round"] = 1
    state["max_rounds"] = 3
    state["scores"] = [
        {"criterion": "innovation", "score": 90, "weight": 0.3, "feedback_he": "", "suggestions": []},
        {"criterion": "market", "score": 55, "weight": 0.2, "feedback_he": "", "suggestions": []},
        {"criterion": "team", "score": 80, "weight": 0.2, "feedback_he": "", "suggestions": []},
    ]
    assert route_after_evaluation(state) == "revise_strategy"


def test_route_after_evaluation_max_rounds():
    """Max rounds reached should force output."""
    state = create_initial_state("X", "Y")
    state["overall_score"] = 70.0
    state["evaluation_round"] = 3
    state["max_rounds"] = 3
    state["scores"] = [
        {"criterion": "innovation", "score": 65, "weight": 0.3, "feedback_he": "", "suggestions": []},
    ]
    assert route_after_evaluation(state) == "max_rounds_reached"


if __name__ == "__main__":
    test_create_initial_state()
    test_route_eligibility_pass()
    test_route_eligibility_fail()
    test_route_after_evaluation_approved()
    test_route_after_evaluation_revise_technical()
    test_route_after_evaluation_revise_strategy()
    test_route_after_evaluation_max_rounds()
    print("✅ All pipeline tests passed!")
