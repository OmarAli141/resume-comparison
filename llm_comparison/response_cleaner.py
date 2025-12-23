def clean_llm_response(response: str) -> str:
    """
    Clean LLM response to extract valid JSON.
    
    Args:
        response: Raw LLM response string
    
    Returns:
        Cleaned JSON string
    """
    resp = response.strip()
    
    # Remove markdown code blocks
    if "```json" in resp:
        resp = resp.split("```json")[1].split("```")[0].strip()
    elif "```" in resp:
        resp = resp.split("```")[1]
        if resp.startswith("json"):
            resp = resp[4:].strip()
        resp = resp.split("```")[0].strip()
    
    # Find JSON array start
    if "[" in resp:
        start = resp.find("[")
        resp = resp[start:]
        # Find matching closing bracket
        bracket_count = 0
        end_pos = -1
        for i, char in enumerate(resp):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_pos = i + 1
                    break
        if end_pos > 0:
            resp = resp[:end_pos]
    
    return resp

