import os
from typing import Dict, Any

def generate_explanation(candidate: dict, jd_requirements: dict, scores_dict: dict) -> str:
    """
    Deterministic template-based generator for candidate explanations matching the exact hackathon spec.
    """
    req_skills = set(s.lower() for s in jd_requirements.get("required_skills", []))
    cand_skills = set(s.lower() for s in candidate.get("skills", []))
    
    total = len(req_skills) if req_skills else 1
    matched = list(req_skills.intersection(cand_skills))
    n = len(matched)
    
    coverage = n / total
    
    top_2 = matched[:2] if len(matched) >= 2 else matched
    top_2_str = ", ".join(top_2) if top_2 else "key skills"
    
    exp = candidate.get("experience_years", 0)
    domain = jd_requirements.get("industry_domain", "the industry")
    
    missing = list(req_skills.difference(cand_skills))
    gap_note = f", missing {missing[0]}" if missing else ""
    
    if coverage >= 0.8:
        return f"Directly matches {n} of {total} required skills including {top_2_str}, {exp} years experience."
    elif coverage >= 0.5:
        return f"Strong semantic alignment in {domain}, covers {n} required skills, {exp} years experience{gap_note}."
    else:
        top_skill = list(cand_skills)[0] if cand_skills else "general tech"
        missing_skill = missing[0] if missing else "required areas"
        return f"Relevant background in {domain} with transferable skills in {top_skill}, may require upskilling in {missing_skill}."

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
