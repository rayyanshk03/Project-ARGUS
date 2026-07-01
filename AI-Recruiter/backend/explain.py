import os
import json
import hashlib
from typing import Dict, Any
import sys

# Ensure we can import modules if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser import connect_db

def get_job_candidate_hash(candidate_id: str, jd_requirements: dict) -> str:
    """Generate a unique deterministic hash for a job + candidate pair for caching."""
    jd_str = json.dumps(jd_requirements, sort_keys=True)
    pair_str = f"{candidate_id}::{jd_str}"
    return hashlib.md5(pair_str.encode('utf-8')).hexdigest()

def generate_explanation(candidate: dict, jd_requirements: dict, scores_dict: dict) -> str:
    """
    Deterministic template-based generator for candidate explanations.
    Replaces the LLM to run safely on CPU without network within 5 minutes.
    """
    db = connect_db()
    explanations_col = db["explanations"]
    
    candidate_id = str(candidate.get("_id", candidate.get("candidate_id", "")))
    cache_key = get_job_candidate_hash(candidate_id, jd_requirements)
    
    # Check MongoDB Cache first
    cached = explanations_col.find_one({"_id": cache_key})
    if cached and "explanation" in cached:
        return cached["explanation"]

    req_skills = set(s.lower() for s in jd_requirements.get("required_skills", []))
    cand_skills = set(s.lower() for s in candidate.get("skills", []))
    
    matched = list(req_skills.intersection(cand_skills))
    missing = list(req_skills.difference(cand_skills))
    
    exp = float(candidate.get("experience_years", 0))
    jd_exp = float(jd_requirements.get("min_experience_years", 0))
    
    bullets = []
    
    # 1. Experience Bullet
    if exp >= jd_exp and jd_exp > 0:
        bullets.append(f"- Exceeds minimum experience requirement ({exp} vs {jd_exp} yrs).")
    elif exp > 0:
        bullets.append(f"- Has {exp} years of experience.")
    else:
        bullets.append("- Experience level not specified or entry-level.")
        
    # 2. Skills Bullet
    if matched:
        if len(matched) > 3:
            bullets.append(f"- Strong skill match, including {', '.join(matched[:3])} and others.")
        else:
            bullets.append(f"- Matches required skills: {', '.join(matched)}.")
    
    # 3. Missing Bullet
    if missing:
        if len(missing) > 2:
            bullets.append(f"- Lacks some required skills like {', '.join(missing[:2])}.")
        else:
            bullets.append(f"- Missing skills: {', '.join(missing)}.")
            
    # 4. Overall Fit
    final_score = scores_dict.get("final_score", 0)
    if final_score > 0.8:
        fit = "Excellent"
    elif final_score > 0.6:
        fit = "Good"
    elif final_score > 0.4:
        fit = "Moderate"
    else:
        fit = "Weak"
        
    bullets.append(f"- Overall fit: {fit}")
    
    explanation = "\n".join(bullets)
    
    # Cache the result
    try:
        explanations_col.update_one(
            {"_id": cache_key},
            {"$set": {
                "candidate_id": candidate_id, 
                "jd_requirements": jd_requirements,
                "scores_dict": scores_dict,
                "explanation": explanation
            }},
            upsert=True
        )
    except Exception as e:
        print(f"Failed to cache explanation in Mongo: {e}")

    return explanation

def generate_skill_gap_summary(candidate: dict, jd_requirements: dict) -> Dict[str, Any]:
    """
    Returns a short structured object analyzing the skill gap locally.
    """
    req_skills = set(s.lower() for s in jd_requirements.get("required_skills", []))
    nice_skills = set(s.lower() for s in jd_requirements.get("nice_to_have_skills", []))
    cand_skills = set(s.lower() for s in candidate.get("skills", []))
    
    missing_crit = list(req_skills.difference(cand_skills))
    missing_nice = list(nice_skills.difference(cand_skills))
    
    if not missing_crit and not missing_nice:
        sug = "Candidate is a perfect match."
    elif not missing_crit:
        sug = f"Consider upskilling in {missing_nice[0]}." if missing_nice else "Great fit."
    else:
        sug = f"Missing critical requirement: {missing_crit[0]}."
        
    return {
        "missing_critical": missing_crit,
        "missing_nice_to_have": missing_nice,
        "suggestion": sug
    }

if __name__ == "__main__":
    # Quick Test
    mock_cand = {
        "candidate_id": "mock_id_123",
        "name": "Alex Backend",
        "experience_years": 4,
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "certifications": ["AWS Solutions Architect"]
    }
    
    mock_jd = {
        "required_skills": ["Python", "FastAPI", "Docker", "AWS"],
        "nice_to_have_skills": ["Kubernetes"],
        "min_experience_years": 5
    }
    
    mock_scores = {
        "semantic_score": 0.85,
        "skill_match_score": 0.75,
        "experience_match_score": 0.80,
        "behavior_score": 0.95,
        "final_score": 0.81
    }
    
    print("=== Testing Explanation Generation ===")
    explanation = generate_explanation(mock_cand, mock_jd, mock_scores)
    print("\nExplanation:\n" + explanation)
    
    print("\n=== Testing Skill Gap Summary ===")
    gaps = generate_skill_gap_summary(mock_cand, mock_jd)
    print(json.dumps(gaps, indent=2))
