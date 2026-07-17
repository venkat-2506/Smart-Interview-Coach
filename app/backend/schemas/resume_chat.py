"""Pydantic schemas for the Resume Knowledge Assistant chat endpoint."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="Either 'user' or 'assistant'.")
    content: str = Field(..., description="The message text.")


class ResumeChatRequest(BaseModel):
    """Request body for POST /resume/{id}/chat."""

    question: str = Field(..., min_length=1, description="The user's question.")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation turns (most recent last).",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Chunks to retrieve.")


class ResumeChatResponse(BaseModel):
    """Response returned by the Resume Knowledge Assistant."""

    answer: str = Field(..., description="The AI-generated answer.")
    is_off_topic: bool = Field(
        default=False,
        description="True if the question was rejected by the guardrail.",
    )
