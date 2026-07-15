"""Prompt templates for resume intelligence.

Keeping prompts in a dedicated module makes them easy to find,
review, and improve without touching business logic.
Each function returns a complete, ready-to-send prompt string.
"""


def build_resume_analysis_prompt(resume_text: str) -> str:
    """Build the prompt that asks Gemini to extract structured data from a resume.

    The prompt explicitly instructs Gemini to return valid JSON only,
    with a defined schema. This keeps the AI output predictable.

    Args:
        resume_text: The plain text extracted from the PDF resume.

    Returns:
        A complete prompt string ready to send to Gemini.
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
    """Build the prompt that asks Gemini to identify the best-fit job role.

    Args:
        resume_text: The plain text extracted from the PDF resume.

    Returns:
        A complete prompt string ready to send to Gemini.
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
    """Build the prompt that asks Gemini to extract and categorize all skills.

    Args:
        resume_text: The plain text extracted from the PDF resume.

    Returns:
        A complete prompt string ready to send to Gemini.
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
