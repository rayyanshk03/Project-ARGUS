import os
import re
import json
from typing import Dict, List, Any

# Dictionary covering common tech skills and their aliases
# Expanding this improves skill match recall significantly.
skills_synonyms = {
    "python": ["python3", "py"],
    "javascript": ["js", "es6", "ecmascript"],
    "typescript": ["ts"],
    "java": ["java 8", "java 11", "java 17", "j2ee"],
    "c#": ["csharp", "c sharp", ".net", "dotnet"],
    "c++": ["cpp", "cplusplus", "c/c++"],
    "go": ["golang"],
    "ruby": ["ruby on rails", "ror"],
    "php": ["laravel", "symfony"],
    "react": ["reactjs", "react.js", "react native"],
    "angular": ["angularjs", "angular.js", "angular 2+"],
    "vue": ["vuejs", "vue.js", "vue3"],
    "node.js": ["node", "nodejs", "node js"],
    "django": ["django rest framework", "drf"],
    "flask": [],
    "spring": ["spring boot", "springboot"],
    "express": ["express.js", "expressjs"],
    "fastapi": ["fast api"],
    "html": ["html5", "html/css"],
    "css": ["css3"],
    "sass": ["scss"],
    "tailwind": ["tailwindcss", "tailwind css"],
    "bootstrap": [],
    "sql": ["mysql", "postgresql", "postgres", "sql server", "mssql", "oracle", "pl/sql"],
    "postgresql": ["postgres", "pg"],
    "nosql": ["mongodb", "mongo", "cassandra", "couchdb", "dynamodb"],
    "mongodb": ["mongo", "mongo db"],
    "redis": [],
    "elasticsearch": ["elastic search", "elk"],
    "docker": ["docker container", "docker-compose"],
    "kubernetes": ["k8s"],
    "aws": ["amazon web services", "ec2", "s3"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "terraform": [],
    "ansible": [],
    "jenkins": [],
    "gitlab ci": ["gitlab ci/cd", "gitlab-ci"],
    "github actions": [],
    "linux": ["ubuntu", "centos", "debian", "unix"],
    "git": ["github", "gitlab", "bitbucket", "version control"],
    "machine learning": ["ml", "machine-learning"],
    "artificial intelligence": ["ai"],
    "deep learning": ["dl"],
    "nlp": ["natural language processing"],
    "computer vision": ["cv"],
    "tensorflow": ["tf"],
    "pytorch": ["torch"],
    "scikit-learn": ["sklearn"],
    "pandas": [],
    "numpy": [],
    "apache spark": ["spark", "pyspark"],
    "kafka": ["apache kafka"],
    "hadoop": [],
    "graphql": [],
    "rest": ["restful", "rest api", "rest APIs"],
    "microservices": ["micro-services", "micro services"]
}

def expand_skills_with_synonyms(skills_list: List[str]) -> List[str]:
    """
    Expands a list of skills by including all known aliases/synonyms.
    Prevents missing candidates who list skills differently (e.g., 'k8s' vs 'kubernetes').
    """
    expanded = set()
    
    # Precompute alias groups to quickly find related terms
    alias_to_group = {}
    for canonical, aliases in skills_synonyms.items():
        group = {canonical.lower()} | {a.lower() for a in aliases}
        for term in group:
            alias_to_group[term] = group

    for skill in skills_list:
        s = skill.lower().strip()
        expanded.add(s)
        if s in alias_to_group:
            expanded.update(alias_to_group[s])
            
    return list(expanded)

def parse_fixed_jd(jd_path: str = "../data/job_description.md") -> Dict[str, Any]:
    """
    Parses a fixed-format Job Description markdown file provided by the hackathon.
    Extracts explicit fields for ranking and writes them to a JSON file.
    
    NOTE: You can hand-tune the regex patterns below based on the actual 
    structure of the provided job_description.md file.
    """
    if not os.path.exists(jd_path):
        print(f"Warning: JD file not found at {jd_path}. Returning empty parsed JD.")
        return {}
        
    with open(jd_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parsed = {
        "role_title": "",
        "seniority_level": "",
        "required_skills": [],
        "nice_to_have_skills": [],
        "min_experience_years": 0,
        "industry_domain": "",
        "soft_skills_mentioned": [],
        "education_requirement": "",
        "certifications_mentioned": [],
        "location_requirement": "",
        "remote_allowed": False,
        "special_notes": ""
    }

    # 1. Extract Role Title
    title_match = re.search(r'(?i)(?:role|title|position):\s*(.+)', content)
    if title_match:
        parsed["role_title"] = title_match.group(1).strip()
        
    # 2. Extract Seniority Level
    seniority_match = re.search(r'(?i)seniority(?: level)?:\s*(.+)', content)
    if seniority_match:
        parsed["seniority_level"] = seniority_match.group(1).strip()
    elif "senior" in parsed["role_title"].lower() or "lead" in parsed["role_title"].lower():
        parsed["seniority_level"] = "Senior"
        
    # 3. Extract Min Experience
    exp_match = re.search(r'(?i)(\d+)(?:\+|-?\d+)?\s*years?(?:\s+of)?\s+experience', content)
    if exp_match:
        parsed["min_experience_years"] = int(exp_match.group(1))
        
    # 4. Extract Industry Domain
    domain_match = re.search(r'(?i)(?:industry|domain):\s*(.+)', content)
    if domain_match:
        parsed["industry_domain"] = domain_match.group(1).strip()
        
    # 5. Extract Location & Remote
    loc_match = re.search(r'(?i)location:\s*(.+)', content)
    if loc_match:
        parsed["location_requirement"] = loc_match.group(1).strip()
        if "remote" in parsed["location_requirement"].lower():
            parsed["remote_allowed"] = True
    if re.search(r'(?i)\bremote\b', content):
        parsed["remote_allowed"] = True
        
    # 6. Extract Education
    edu_match = re.search(r'(?i)(?:education|degree):\s*(.+)', content)
    if edu_match:
        parsed["education_requirement"] = edu_match.group(1).strip()

    # 7. Extract Hackathon Special Notes
    # Looks for a section explicitly titled "Specifically for hackathon participants"
    notes_match = re.search(r'(?i)specifically for hackathon participants[^\n]*\n(.*?)(?=\n#|$)', content, re.DOTALL)
    if notes_match:
        parsed["special_notes"] = notes_match.group(1).strip()
        
    # 8. Extract Required Skills
    req_skills_match = re.search(r'(?i)required skills:(.*?)(?=\n\n|\n#|$)', content, re.DOTALL)
    if req_skills_match:
        skills_text = req_skills_match.group(1)
        raw_skills = [s.strip(" *-") for s in re.split(r'[,|\n]', skills_text) if s.strip(" *-")]
        parsed["required_skills"] = expand_skills_with_synonyms(raw_skills)
        
    # 9. Extract Nice-to-Have Skills
    nice_skills_match = re.search(r'(?i)(?:nice to have|preferred) skills:(.*?)(?=\n\n|\n#|$)', content, re.DOTALL)
    if nice_skills_match:
        skills_text = nice_skills_match.group(1)
        raw_skills = [s.strip(" *-") for s in re.split(r'[,|\n]', skills_text) if s.strip(" *-")]
        parsed["nice_to_have_skills"] = expand_skills_with_synonyms(raw_skills)
        
    # 10. Extract Soft Skills (Basic heuristic)
    soft_skills_keywords = ["communication", "leadership", "teamwork", "problem solving", "mentoring", "agile"]
    found_soft_skills = [s for s in soft_skills_keywords if s.lower() in content.lower()]
    parsed["soft_skills_mentioned"] = found_soft_skills

    # Write the parsed schema to JSON for other modules to load instantly
    output_path = os.path.join(os.path.dirname(jd_path), "parsed_jd.json")
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=4)
        print(f"Successfully parsed JD and saved structured output to {output_path}")
    except Exception as e:
        print(f"Error saving parsed JD to {output_path}: {e}")

    return parsed

if __name__ == "__main__":
    # Example execution
    test_jd_path = os.path.join(os.path.dirname(__file__), "..", "data", "job_description.md")
    
    # If it doesn't exist, we can mock it for testing purposes
    if not os.path.exists(test_jd_path):
        print(f"Creating a mock {test_jd_path} for testing...")
        os.makedirs(os.path.dirname(test_jd_path), exist_ok=True)
        with open(test_jd_path, 'w', encoding='utf-8') as f:
            f.write("""# Role: Senior ML Engineer
Location: Remote (US)
Industry: AI & Tech

## Required Skills:
- Python
- k8s
- ML
- PostgreSQL

## Nice to have Skills:
- React
- AWS

## Experience
Minimum 5 years of experience in production ML systems.

## Specifically for hackathon participants
Must heavily weight candidates with open source contributions.
""")

    parsed_result = parse_fixed_jd(test_jd_path)
    print("\nParsed Result:")
    print(json.dumps(parsed_result, indent=2))
