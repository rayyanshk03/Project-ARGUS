import re
from typing import Dict, Any

def extract_skills_from_text(text: str) -> list:
    """Simple regex based extraction for common tech skills."""
    common_skills = [
        "python", "java", "c++", "c#", "javascript", "typescript", "react", "angular", "vue", 
        "node", "express", "django", "flask", "fastapi", "spring", "aws", "gcp", "azure",
        "docker", "kubernetes", "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow",
        "pandas", "numpy", "scikit-learn", "data science", "data engineering", "spark", "hadoop",
        "kafka", "rabbitmq", "graphql", "rest", "api", "git", "ci/cd", "jenkins", "github actions",
        "linux", "bash", "shell", "html", "css", "sass", "less", "tailwind", "bootstrap",
        "go", "rust", "ruby", "php", "swift", "kotlin", "dart", "flutter", "react native"
    ]
    
    found_skills = set()
    text_lower = text.lower()
    
    for skill in common_skills:
        # Match whole words only using regex \b
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
            
    return list(found_skills)

def extract_experience_from_text(text: str) -> int:
    """Extracts minimum years of experience using regex."""
    pattern = r'(\d+)\+?\s*(?:-\s*\d+\s*)?years?'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0
    
def extract_role_title(text: str) -> str:
    """Attempts to extract role title from the first sentence or common patterns."""
    text_lower = text.lower()
    roles = ["engineer", "developer", "scientist", "manager", "analyst", "designer", "architect"]
    for role in roles:
        if role in text_lower:
            # Very naive extraction: just find the sentence containing the role
            sentences = text.split('.')
            for s in sentences:
                if role in s.lower():
                    words = s.strip().split()
                    # take up to 5 words around the role
                    idx = -1
                    for i, w in enumerate(words):
                        if role in w.lower():
                            idx = i
                            break
                    if idx != -1:
                        start = max(0, idx - 2)
                        end = min(len(words), idx + 2)
                        return " ".join(words[start:end]).title()
    return "Software Professional"

def understand_job_description(jd_text: str) -> Dict[str, Any]:
    """Parses a raw job description into structured JSON locally using rules."""
    skills = extract_skills_from_text(jd_text)
    
    # Split skills arbitrarily if we want nice_to_have, but for simplicity:
    req_skills = skills[:int(len(skills)*0.7)] if len(skills) > 3 else skills
    nice_skills = skills[int(len(skills)*0.7):] if len(skills) > 3 else []
    
    return {
        "role_title": extract_role_title(jd_text),
        "seniority_level": "senior" if "senior" in jd_text.lower() else ("junior" if "junior" in jd_text.lower() else "mid"),
        "required_skills": req_skills,
        "nice_to_have_skills": nice_skills,
        "min_experience_years": extract_experience_from_text(jd_text),
        "industry_domain": "",
        "soft_skills": [],
        "education_requirement": "bachelor" if "bachelor" in jd_text.lower() else None,
        "certifications_preferred": [],
        "location_requirement": None,
        "remote_allowed": "remote" in jd_text.lower()
    }

def natural_language_query_to_filters(query_text: str) -> Dict[str, Any]:
    """Translates NL query to filters using the same local rule-based approach."""
    return understand_job_description(query_text)

if __name__ == "__main__":
    test_jd = "Looking for Senior Backend Engineer with FastAPI, AWS, Docker. Must have led a team before. 5+ years experience required."
    print("--- Testing local rule-based parser ---")
    print(f"INPUT: {test_jd}\n")
    
    import json
    parsed = understand_job_description(test_jd)
    print("OUTPUT (JSON):")
    print(json.dumps(parsed, indent=2))

