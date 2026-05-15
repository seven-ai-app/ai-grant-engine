from langgraph.graph import StateGraph, END

from .state import GrantState
from .nodes import (
    ingest_node,
    eligibility_node,
    strategist_node,
    technical_writer_node,
    cfo_node,
    red_team_node,
    output_node,
)
from .edges import route_eligibility, route_after_evaluation


def build_grant_pipeline() -> StateGraph:
    graph = StateGraph(GrantState)

    # Add all nodes
    graph.add_node("ingest", ingest_node)
    graph.add_node("check_eligibility", eligibility_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("technical_writer", technical_writer_node)
    graph.add_node("cfo", cfo_node)
    graph.add_node("red_team", red_team_node)
    graph.add_node("generate_output", output_node)

    # Set entry point
    graph.set_entry_point("ingest")

    # Linear flow: ingest -> eligibility check
    graph.add_edge("ingest", "check_eligibility")

    # Conditional: eligible or rejected
    graph.add_conditional_edges(
        "check_eligibility",
        route_eligibility,
        {"eligible": "strategist", "not_eligible": END},
    )

    # Linear flow: strategist -> technical -> cfo -> red team
    graph.add_edge("strategist", "technical_writer")
    graph.add_edge("technical_writer", "cfo")
    graph.add_edge("cfo", "red_team")

    # Red Team routing: approved, revise, or max rounds
    graph.add_conditional_edges(
        "red_team",
        route_after_evaluation,
        {
            "approved": "generate_output",
            "revise_strategy": "strategist",
            "revise_technical": "technical_writer",
            "revise_budget": "cfo",
            "max_rounds_reached": "generate_output",
        },
    )

    # Output -> done
    graph.add_edge("generate_output", END)

    return graph


def compile_pipeline():
    graph = build_grant_pipeline()
    return graph.compile()
