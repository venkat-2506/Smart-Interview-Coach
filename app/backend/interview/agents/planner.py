"""Planner Agent implementation."""

from loguru import logger

from app.ai.llm.client import get_llm_json_response
from app.backend.interview.prompts import build_planner_prompt
from app.backend.interview.state import InterviewState


class PlannerAgent:
    """Agent responsible for designing a customized, dynamic interview plan.

    Planner inspects the candidate's resume context, job role, and mode
    to decide the structure of stages, topics, and question counts.
    """

    def plan(self, state: InterviewState) -> dict:
        """Generate a dynamic plan and update the state.

        Args:
            state: Current LangGraph state.

        Returns:
            Dict containing state modifications (specifically 'interview_plan' and 'remaining_plan').
        """
        logger.info(
            f"Planner Agent starting plan generation for role={state['selected_role']}, mode={state['interview_mode']}"
        )

        prompt = build_planner_prompt(
            resume_text=state["resume_context"],
            role=state["selected_role"],
            mode=state["interview_mode"],
        )

        try:
            plan_dict = get_llm_json_response(prompt)
            # Validate plan structure
            if not isinstance(plan_dict, dict) or "plan" not in plan_dict:
                raise ValueError("LLM response did not contain 'plan' list.")
            
            plan_list = plan_dict["plan"]
            if not isinstance(plan_list, list) or len(plan_list) == 0:
                raise ValueError("LLM response 'plan' field is not a non-empty list.")
            
            logger.info(f"Planner Agent generated dynamic plan with {len(plan_list)} stages.")
            return {
                "interview_plan": plan_dict,
                "remaining_plan": plan_list,
            }
        except Exception as e:
            logger.error(f"Planner Agent failed to generate dynamic plan: {e}")
            # Safe fallback plan if LLM fails
            fallback_plan = {
                "plan": [
                    {
                        "stage": "resume_discussion",
                        "question_count": 2,
                        "topics": ["general introduction", "experience alignment"],
                        "difficulty": "medium",
                    },
                    {
                        "stage": "technical",
                        "question_count": 2,
                        "topics": ["core technologies", "role-specific problems"],
                        "difficulty": "medium",
                    },
                ]
            }
            logger.info("Planner Agent falling back to static default plan.")
            return {
                "interview_plan": fallback_plan,
                "remaining_plan": fallback_plan["plan"],
            }
