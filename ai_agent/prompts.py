"""
Centralized prompt templates for clarity and reusability.
"""

QUESTION_ORDER = [
    "job_title",
    "experience_seniority",
    "skills",
    "education"
]

QUESTION_PROMPTS = {
    "job_title": "What role are you hiring for?",
    "experience_seniority": "What years of experience and/or seniority level? \n",
    "skills": "What specific skills are required? (comma-separated or 'skip' if open)\n",
    "education": "What is the minimum education level? (Bachelor's, Master's, PhD, or 'skip')\n"
}

SKIP_KEYWORDS = [
    "open", "skip", "any", "flexible", "no preference", 
    "doesn't matter", "doesnt matter", "not required", "none"
]

SENIORITY_MAP = {
    "intern": "Intern/Student",
    "junior": "Junior",
    "jr": "Junior",
    "mid": "Mid-level",
    "mid-level": "Mid-level",
    "midlevel": "Mid-level",
    "senior": "Senior",
    "sr": "Senior",
    "lead": "Lead / Principal",
    "principal": "Lead / Principal",
    "manager": "Manager / Executive",
    "executive": "Manager / Executive",
    "director": "Manager / Executive"
}

EDUCATION_MAP = {
    "bachelor": "Bachelor's",
    "bachelors": "Bachelor's",
    "bs": "Bachelor's",
    "ba": "Bachelor's",
    "b.s": "Bachelor's",
    "b.a": "Bachelor's",
    "master": "Master's",
    "masters": "Master's",
    "ms": "Master's",
    "ma": "Master's",
    "m.s": "Master's",
    "m.a": "Master's",
    "mba": "Master's",
    "phd": "PhD",
    "doctorate": "PhD",
    "doctoral": "PhD"
}