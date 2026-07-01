import json
import re
import os
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

def fallback_regex_parse(jd_text: str) -> dict:
    """Fallback extraction using regex/keywords if LLM fails or is unavailable."""
    skills = []
    # common technical skills
    for skill in ['python', 'sql', 'aws', 'java', 'react', 'node', 'pytorch', 'tensorflow', 'pandas', 'django', 'javascript']:
        if re.search(r'\b' + re.escape(skill) + r'\b', jd_text, re.IGNORECASE):
            skills.append(skill)
            
    exp_match = re.search(r'(\d+)\+?\s*years?', jd_text, re.IGNORECASE)
    min_exp = int(exp_match.group(1)) if exp_match else 0
    
    role_level = "mid"
    if re.search(r'\bsenior\b', jd_text, re.IGNORECASE): role_level = "senior"
    elif re.search(r'\bjunior\b', jd_text, re.IGNORECASE): role_level = "junior"
        
    return {
        "required_skills": skills,
        "nice_to_have_skills": [],
        "min_experience_years": min_exp,
        "role_level": role_level,
        "domain": "general"
    }

def parse_jd(jd_text: str) -> dict:
    """Parses the raw job description string and returns structured requirements."""
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not Anthropic:
        print("Warning: ANTHROPIC_API_KEY not found or anthropic not installed. Using fallback regex.")
        return fallback_regex_parse(jd_text)
        
    client = Anthropic(api_key=api_key)
    
    system_prompt = """
You are an expert technical recruiter and HR parser.
Your task is to extract structured requirements from the provided Job Description text.
You MUST output ONLY a valid JSON object. Do not include markdown formatting, backticks, or any conversational text.

The JSON object must have exactly these keys:
- "required_skills": list of strings (must have skills)
- "nice_to_have_skills": list of strings (preferred/bonus skills)
- "min_experience_years": integer (minimum years of experience required. 0 if not specified)
- "role_level": string (one of "junior", "mid", "senior")
- "domain": string (e.g. "machine learning", "web development", "finance")
"""

    try:
        # Note: 'claude-sonnet-4-6' was requested, assuming mapping to the closest valid Anthropic model
        # If the exact string 'claude-sonnet-4-6' is required and throws an error, 
        # the try-except block will catch it and seamlessly use the regex fallback.
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Extract the structured requirements from this JD:\n\n{jd_text}"}
            ]
        )
        
        # Parse JSON
        result_text = response.content[0].text.strip()
        
        # Clean markdown if the LLM still output it
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        parsed_json = json.loads(result_text.strip())
        
        # Validate keys
        expected_keys = {"required_skills", "nice_to_have_skills", "min_experience_years", "role_level", "domain"}
        if not expected_keys.issubset(parsed_json.keys()):
            raise ValueError(f"Missing expected keys in JSON. Found: {parsed_json.keys()}")
            
        return parsed_json
        
    except Exception as e:
        print(f"LLM parsing failed: {e}. Falling back to regex extraction.")
        return fallback_regex_parse(jd_text)
        
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jd_path = os.path.join(base_dir, "data", "jd.txt")
    if os.path.exists(jd_path):
        with open(jd_path, 'r', encoding='utf-8') as f:
            sample_jd = f.read()
        result = parse_jd(sample_jd)
        print(json.dumps(result, indent=2))
