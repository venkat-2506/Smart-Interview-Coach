"""Provider-independent LLM client."""

import json
import re

import groq
from groq import Groq
from loguru import logger

from config import get_settings


def get_llm_response(prompt: str) -> str:
    """Send a prompt to the LLM and return the raw text response.

    Args:
        prompt: The full prompt string.

    Returns:
        The text response from the LLM.

    Raises:
        ValueError: If configuration is missing or API call fails.
    """
    settings = get_settings()

    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in configuration.")

    try:
        client = Groq(api_key=settings.groq_api_key)

        logger.info(f"Sending prompt to LLM using model: {settings.groq_model}")

        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )

        logger.info("Received response from LLM.")
        return response.choices[0].message.content or ""

    except groq.AuthenticationError as e:
        logger.error(f"LLM Authentication failed: {e}")
        raise ValueError(f"Authentication failed with LLM provider: {e}") from e
    except groq.RateLimitError as e:
        logger.error(f"LLM Rate limit exceeded: {e}")
        raise ValueError(f"Rate limit exceeded with LLM provider: {e}") from e
    except groq.APIConnectionError as e:
        logger.error(f"LLM Connection error: {e}")
        raise ValueError(f"Connection error with LLM provider: {e}") from e
    except groq.APIStatusError as e:
        logger.error(f"LLM API Status error (status code: {e.status_code}): {e}")
        raise ValueError(f"LLM provider returned status error: {e}") from e
    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        raise ValueError(f"Failed to generate content from LLM: {e}") from e


def get_llm_json_response(prompt: str) -> dict:
    """Send a prompt to the LLM and parse the response as JSON.

    The prompt must explicitly ask the LLM to return valid JSON only.

    Args:
        prompt: The full prompt string. Must instruct the LLM to return JSON.

    Returns:
        A Python dictionary parsed from the JSON response.

    Raises:
        ValueError: If the response is not valid JSON.
        Exception: If the API call fails.
    """
    raw_text = get_llm_response(prompt)

    cleaned_text = raw_text.strip()
    
    # Remove markdown code block syntax if present
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned_text, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned_text = match.group(1).strip()

    try:
        parsed_json = json.loads(cleaned_text)
        return parsed_json
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Raw LLM response was:\n{raw_text}")
        raise ValueError(f"LLM returned invalid JSON: {e}") from e
