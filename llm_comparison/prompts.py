def build_comparative_analysis_prompt(candidates_text: str, job_query: str) -> str:
    return f'''You are a Senior Recruiter with 15+ years of experience hiring for all types of roles.

Job to fill:
"{job_query}"

Here are the top 3 pre-filtered candidates (already passed ATS keyword screening):

{candidates_text}

TASK:
Compare these 3 candidates against the job above and give each one a realistic ATS Fit Score out of 100.

Scoring weights:
- Skills & tools match → 40%
- Relevant experience depth → 25%
- Education & certifications → 15%
- Seniority / level fit → 10%
- Overall profile strength & keywords → 10%

Return ONLY a valid JSON array of exactly 3 objects (one per candidate) using this exact structure:

[
  {{
    "candidate_id": "12345678",
    "ats_fit_score": 92,
    "level_fit": "Strong Junior",
    "overall_summary": "Very strong match with all required skills and perfect experience length for the role.",
    "unique_strengths": [
      "Master's degree in relevant field",
      "Hands-on experience with exactly the tools mentioned in JD",
      "Fast learner with strong recent projects"
    ],
    "key_differentiators_vs_others": "Best combination of technical skills and relevant recent experience",
    "potential_risks": "Limited exposure to enterprise-scale environments",
    "why_choose_this_candidate": "Can start contributing from day one with zero training gap",
    "why_not_choose_others": "Candidate #2 has weaker tool coverage; #3 has shorter relevant experience",
    "final_recommendation": "Strong Hire — Priority interview"
  }}
]

CRITICAL RULES:
- Return valid JSON only → no markdown, no extra text, no explanations
- Use ONLY information that actually appears in the candidate profiles above
- Infer the correct seniority level from years of experience and job titles (e.g. 0–2y = Junior, 3–6y = Mid-level, 7+ = Senior)
- Never invent certifications or companies that are not listed
- Be brutally honest but professional
- The highest ats_fit_score = #1 recommended candidate
- candidate_id must exactly match one of the IDs shown above
'''