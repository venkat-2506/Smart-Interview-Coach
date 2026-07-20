"""Question Generator Agent implementation."""

from loguru import logger

from app.ai.llm.client import get_llm_json_response
from app.backend.interview.prompts import build_question_generator_prompt
from app.backend.interview.state import InterviewState


class QuestionGeneratorAgent:
    """Agent responsible for generating the next interview question.

    Reads the current stage, plan details, and history, then outputs
    a resume-aware interview question and its metadata in JSON.
    """

    def generate(self, state: InterviewState) -> dict:
        """Generate the next question based on current stage and history.

        Args:
            state: Current LangGraph state.

        Returns:
            Dict containing state modifications (specifically 'current_question' and 'new_question_metadata').
        """
        logger.info(
            f"Question Generator Agent generating Q#{state['question_number']} for stage={state['current_stage']}, topic={state['current_topic']}"
        )

        prompt = build_question_generator_prompt(
            resume_text=state["resume_context"],
            role=state["selected_role"],
            stage=state["current_stage"],
            topic=state["current_topic"],
            difficulty=state["current_difficulty"],
            question_number=state["question_number"],
            history=state["interview_history"],
        )

        try:
            metadata = get_llm_json_response(prompt)
            # Validate response schema
            if not isinstance(metadata, dict) or "question" not in metadata:
                raise ValueError("LLM response did not contain 'question' field.")
            
            question_text = metadata["question"]
            logger.info(f"Question Generator Agent successfully generated: {question_text[:50]}...")
            
            return {
                "current_question": question_text,
                "new_question_metadata": {
                    "question": question_text,
                    "question_type": metadata.get("question_type", "technical"),
                    "topic": metadata.get("topic", state["current_topic"]),
                    "difficulty": metadata.get("difficulty", state["current_difficulty"]),
                    "stage": metadata.get("stage", state["current_stage"]),
                },
            }
        except Exception as e:
            logger.error(f"Question Generator Agent failed to generate question: {e}")
            # Fallback question if LLM fails
            fallback_question = f"Can you tell me more about your experience in relation to the role of {state['selected_role']}?"
            fallback_metadata = {
                "question": fallback_question,
                "question_type": "resume",
                "topic": "general background",
                "difficulty": "medium",
                "stage": state["current_stage"],
            }
            logger.info("Question Generator Agent falling back to static question.")
            return {
                "current_question": fallback_question,
                "new_question_metadata": fallback_metadata,
            }
