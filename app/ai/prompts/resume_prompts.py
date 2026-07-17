"""Prompt templates for resume intelligence.

Keeping prompts in a dedicated module makes them easy to find,
review, and improve without touching business logic.
Each function returns a complete, ready-to-send prompt string.
"""


def build_resume_analysis_prompt(resume_text: str) -> str:
    """Build the prompt that asks the LLM to extract structured data from a resume.

    The prompt explicitly instructs the LLM to return valid JSON only,
    with a defined schema. This keeps the AI output predictable.

    Args:
        resume_text: The plain text extracted from the PDF resume.

    Returns:
        A complete prompt string ready to send to the LLM.
    """
    return f"""
You are a professional resume parser. Analyze the resume text below and extract
structured information. Return ONLY valid JSON with no extra text or explanation.

Use this exact JSON structure:
{{
    "full_name": "string",
    "email": "string or null",
    "phone": "string or null",
    "education": [
        {{
            "institution": "string",
            "degree": "string",
            "field": "string",
            "year": "string or null"
        }}
    ],
    "experience": [
        {{
            "company": "string",
            "role": "string",
            "duration": "string or null",
            "description": "string or null"
        }}
    ],
    "projects": [
        {{
            "name": "string",
            "description": "string",
            "technologies": ["string"]
        }}
    ],
    "certifications": ["string"],
    "skills": ["string"],
    "technologies": ["string"]
}}

Rules:
- If a field has no data, use null for strings or [] for arrays.
- Do not invent information. Only extract what is present.
- Return ONLY the JSON object. No markdown, no explanation.

Resume Text:
---
{resume_text}
---
"""


def build_role_detection_prompt(resume_text: str) -> str:
    """Build the prompt that asks the LLM to identify the best-fit job role.

    Args:
        resume_text: The plain text extracted from the PDF resume.

    Returns:
        A complete prompt string ready to send to the LLM.
    """
    return f"""
You are a career advisor AI. Based on the resume text below, identify the most
suitable target job role for this candidate.

Return ONLY valid JSON with this exact structure:
{{
    "primary_role": "string",
    "alternative_roles": ["string", "string"],
    "reason": "string (one or two sentences explaining why)"
}}

Consider roles such as: Software Engineer, Backend Developer, Frontend Developer,
Full Stack Developer, AI Engineer, Machine Learning Engineer, Data Scientist,
Data Analyst, Cloud Engineer, DevOps Engineer, Cybersecurity Engineer, etc.

Rules:
- Return ONLY the JSON object. No markdown, no explanation.
- Be specific. Do not return generic roles like "Engineer".

Resume Text:
---
{resume_text}
---
"""


def build_skill_extraction_prompt(resume_text: str) -> str:
    """Build the prompt that asks the LLM to extract and categorize all skills.

    Args:
        resume_text: The plain text extracted from the PDF resume.

    Returns:
        A complete prompt string ready to send to the LLM.
    """
    return f"""
You are a technical skills extractor. Analyze the resume text below and
categorize all skills mentioned.

Return ONLY valid JSON with this exact structure:
{{
    "programming_languages": ["string"],
    "frameworks": ["string"],
    "libraries": ["string"],
    "databases": ["string"],
    "cloud_platforms": ["string"],
    "developer_tools": ["string"],
    "soft_skills": ["string"]
}}

Rules:
- If no skills exist for a category, return an empty array [].
- Do not duplicate items across categories.
- Return ONLY the JSON object. No markdown, no explanation.

Resume Text:
---
{resume_text}
---
"""


def build_guardrail_prompt(question: str) -> str:
    """Build a prompt to classify whether a question is relevant to resume/career topics.

    Args:
        question: The user's question to validate.

    Returns:
        A prompt string that instructs the LLM to return "RELEVANT" or "OFF_TOPIC".
    """
    return f"""You are a strict topic classifier for a Resume Knowledge Assistant.

Your only job is to decide whether the following question is relevant or not.

RELEVANT topics:
- Resume content (experience, education, projects, skills, certifications)
- Interview preparation (HR questions, behavioral questions, technical questions)
- Technical concepts mentioned in a resume (e.g., SQL, Python, Machine Learning)
- Career guidance (strengths, weaknesses, missing skills, career path)
- Self-introduction tips

OFF_TOPIC topics (reject these):
- Weather, news, politics, sports, movies, entertainment
- General coding tasks unrelated to the user's resume
- Casual chitchat or unrelated general knowledge

Respond with EXACTLY one word: RELEVANT or OFF_TOPIC

Question: {question}
"""


def build_chat_prompt(
    question: str,
    context_chunks: list[str],
    history: list[dict],
) -> str:
    """Build the conversational prompt for the Resume Knowledge Assistant.

    Args:
        question: The user's current question.
        context_chunks: List of relevant resume text chunks retrieved by RAG.
        history: Previous conversation as a list of {{"role": ..., "content": ...}} dicts.

    Returns:
        A complete prompt string ready to send to the LLM.
    """
    context = "\n\n".join(context_chunks) if context_chunks else "No specific resume context retrieved."

    history_text = ""
    if history:
        turns = []
        for msg in history[-6:]:  # Keep last 6 turns (3 exchanges) to stay within context
            role_label = "User" if msg["role"] == "user" else "Assistant"
            turns.append(f"{role_label}: {msg['content']}")
        history_text = "\n".join(turns)

    return f"""You are a professional Resume Knowledge Assistant for interview preparation.

Your role is to help the user understand their resume, prepare for interviews, explain
technical concepts from their resume, and provide career guidance.

RESUME CONTEXT (retrieved sections relevant to the question):
---
{context}
---

CONVERSATION HISTORY:
{history_text if history_text else "(No previous conversation)"}

USER QUESTION:
{question}

INSTRUCTIONS:
- Answer based primarily on the resume context provided above.
- If the context does not contain enough information to answer, clearly say so.
  Do NOT invent or hallucinate details that are not in the resume.
- For technical concept questions (e.g., "Explain SQL"), explain the concept clearly,
  relate it to how it appears in the user's resume, and give interview tips.
- For interview preparation questions, generate professional, targeted questions or tips.
- Be concise but thorough. Use bullet points where appropriate for readability.
- Always maintain a professional, encouraging, interview-coaching tone.
- Do NOT mention chunk IDs, similarity scores, or internal retrieval details.
- Consider the conversation history for follow-up questions.

Provide a clear, helpful answer:"""

