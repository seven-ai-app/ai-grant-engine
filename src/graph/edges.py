from .state import GrantState
from ..config.constants import MINIMUM_PASSING_SCORE


def route_eligibility(state: GrantState) -> str:
    if state["is_eligible"]:
        return "eligible"
    return "not_eligible"


def route_after_evaluation(state: GrantState) -> str:
    if state["overall_score"] >= MINIMUM_PASSING_SCORE:
        return "approved"

    if state["evaluation_round"] >= state["max_rounds"]:
        return "max_rounds_reached"

    # Find weakest criterion and route to responsible agent
    if not state["scores"]:
        return "approved"

    weakest = min(state["scores"], key=lambda s: s["score"])
    criterion = weakest["criterion"]

    routing_map = {
        "innovation": "revise_technical",
        "feasibility": "revise_technical",
        "market": "revise_strategy",
        "team": "revise_strategy",
        "grant_contribution": "revise_budget",
    }

    return routing_map.get(criterion, "revise_strategy")
