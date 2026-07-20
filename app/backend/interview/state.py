"""LangGraph state representation for the Interview Engine workflow."""

from typing import TypedDict, List, Dict, Any, Optional


class InterviewState(TypedDict):
    """Represents the complete state of the interview workflow.

    This state is updated by agents inside LangGraph and persists
    across graph execution transitions. It's designed to support
    future Evaluation, Memory, and Decision agents seamlessly.
    """

    resume_context: str
    selected_role: str
    interview_mode: str

    # The dynamic planner plans (list of stages with question counts)
    interview_plan: Dict[str, Any]
    remaining_plan: List[Dict[str, Any]]
    covered_topics: List[str]

    # Conversation tracking
    interview_history: List[Dict[str, Any]]
    question_number: int

    # Current question details
    current_stage: str
    current_topic: str
    current_difficulty: str
    current_question: str

    # Rich metadata returned by the Question Generator agent
    new_question_metadata: Optional[Dict[str, Any]]
