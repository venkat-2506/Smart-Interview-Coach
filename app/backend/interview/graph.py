"""LangGraph workflow definition for the Interview Engine."""

from loguru import logger
from langgraph.graph import StateGraph, START, END

from app.backend.interview.state import InterviewState
from app.backend.interview.agents.planner import PlannerAgent
from app.backend.interview.agents.question_generator import QuestionGeneratorAgent


def planner_node(state: InterviewState) -> dict:
    """Invokes the Planner Agent node in LangGraph."""
    logger.info("Running LangGraph planner node.")
    agent = PlannerAgent()
    return agent.plan(state)


def question_generator_node(state: InterviewState) -> dict:
    """Invokes the Question Generator Agent node in LangGraph."""
    logger.info("Running LangGraph question_generator node.")
    agent = QuestionGeneratorAgent()
    return agent.generate(state)


def persist_state_node(state: InterviewState) -> dict:
    """Node indicating that state is processed and prepared for database sync."""
    logger.info("Running LangGraph persist_state node.")
    # This node confirms states are fully evaluated and updated in memory.
    # The service layer performs actual database persistence, matching S2 boundaries.
    return {}


def route_planner(state: InterviewState) -> str:
    """Decide whether to run the planner based on state context."""
    if not state.get("interview_plan"):
        logger.info("No interview plan found in state. Routing to 'planner' node.")
        return "planner"
    logger.info("Interview plan already exists in state. Skipping planner; routing to 'question_generator'.")
    return "question_generator"


def create_interview_graph():
    """Build and compile the modular LangGraph workflow.

    Workflow Structure:
    START -> (conditional) -> planner -> question_generator -> persist_state -> END
    """
    workflow = StateGraph(InterviewState)

    # Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("question_generator", question_generator_node)
    workflow.add_node("persist_state", persist_state_node)

    # Add Conditional Edges from START
    workflow.add_conditional_edges(
        START,
        route_planner,
        {
            "planner": "planner",
            "question_generator": "question_generator"
        }
    )

    # Add Directed Edges
    workflow.add_edge("planner", "question_generator")
    workflow.add_edge("question_generator", "persist_state")
    workflow.add_edge("persist_state", END)

    return workflow.compile()


# Export compiled graph instance
interview_graph = create_interview_graph()
