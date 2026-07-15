"""Google Gemini LLM client wrapper.

This module provides a single, reusable function for calling the
Gemini model. All AI modules in this project import from here.
That way, if we ever change models or providers, we only update
this one file.
"""

import json

from google import genai
from loguru import logger

from config import get_settings


def get_gemini_response(prompt: str) -> str:
    """Send a prompt to Gemini and return the raw text response.

    Args:
        prompt: The full prompt string to send to the model.

    Returns:
        The model's text response as a plain string.

    Raises:
        Exception: If the Gemini API call fails.
    """
    settings = get_settings()

    # Configure the new Gemini client with our API key from settings
    client = genai.Client(api_key=settings.gemini_api_key)

    logger.info(f"Sending prompt to Gemini using model: {settings.gemini_model}")
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise ValueError(f"Failed to generate content from Gemini: {e}") from e

    logger.info("Received response from Gemini.")

    return response.text


def get_gemini_json_response(prompt: str) -> dict:
    """Send a prompt to Gemini and parse the response as JSON.

    This is the primary function used for structured resume analysis.
    The prompt must explicitly ask Gemini to return valid JSON only.

    Args:
        prompt: The full prompt string. Must instruct Gemini to return JSON.

    Returns:
        A Python dictionary parsed from the Gemini JSON response.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.
        Exception: If the Gemini API call fails.
    """
    raw_text = get_gemini_response(prompt)

    # Gemini sometimes wraps JSON in markdown code blocks like ```json ... ```
    # We strip those markers to extract clean JSON
    cleaned_text = raw_text.strip()
    if cleaned_text.startswith("```"):
        # Remove the opening ```json or ``` line
        cleaned_text = cleaned_text.split("\n", 1)[-1]
        # Remove the closing ```
        cleaned_text = cleaned_text.rsplit("```", 1)[0]
        cleaned_text = cleaned_text.strip()

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.error(f"Raw response was: {raw_text[:500]}")
        raise ValueError(f"Gemini returned invalid JSON: {e}") from e

    return result
