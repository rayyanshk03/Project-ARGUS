import numpy as np
import pandas as pd
import re
from typing import List, Dict, Any, Tuple

def detect_honeypot(candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons = []
    
    # Extract variables
    profile = candidate.get("profile", {})
    exp_years = float(candidate.get("experience_years", 0) or 0)
    skills = candidate.get("skills", [])
    if isinstance(skills, list) and len(skills) > 0 and isinstance(skills[0], dict):
        # Handle dict format
        skills_len = len(skills)
    elif isinstance(skills, list):
        skills_len = len(skills)
    else:
        skills_len = 0
        
    signals = candidate.get("redrob_signals", {})
    
    # 1. Experience-age mismatch
    # Try to find graduation year
    grad_year = None
    education = candidate.get("education", [])
    for ed in education:
        if isinstance(ed, dict):
            # look for dates
            end_date = str(ed.get("end_date", ed.get("graduation_year", "")))
            match = re.search(r'(19|20)\d{2}', end_date)
            if match:
                y = int(match.group())
                if grad_year is None or y > grad_year:
                    grad_year = y
                    
    if grad_year:
        # Approximate age assuming grad at 22
        current_year = 2026 # assuming current time context
        approx_age = 22 + (current_year - grad_year)
        if exp_years > (approx_age - 18):
            score += 0.4
            reasons.append(f"Experience-age mismatch: {exp_years} yrs exp, approx age {approx_age}.")
            
    # 2. Skills-experience depth mismatch
    if skills_len >= 50 and exp_years <= 2.0:
        score += 0.4
        reasons.append(f"Depth mismatch: {skills_len} skills but only {exp_years} years exp.")
        
    # 3. All behavioral signals maxed out
    if signals:
        maxed = 0
        total = 0
        for k, v in signals.items():
            if isinstance(v, (int, float)):
                total += 1
                if v >= 99.0 or v >= 0.99: # Handling both 0-1 and 0-100 scales generically
                    # Many fields like response rate max out at 1.0, completeness at 100, views at 999
                    maxed += 1
        if total > 5 and (maxed / total) > 0.8:
            score += 0.5
            reasons.append(f"Synthetic signals: {maxed}/{total} signals are near maximum.")
            
    # 4. Salary/level mismatch
    headline = profile.get("headline", "").lower()
    title = ""
    career = candidate.get("career_history", [])
    if career and isinstance(career, list) and len(career) > 0 and isinstance(career[0], dict):
        title = career[0].get("title", "").lower()
        
    is_senior = "senior" in headline or "lead" in headline or "senior" in title or "lead" in title
    if is_senior and exp_years <= 2.0:
        score += 0.3
        reasons.append(f"Level mismatch: Claims Senior/Lead with {exp_years} years exp.")
        
    # 5. Round number syndrome
    if exp_years > 0 and exp_years % 5 == 0 and exp_years >= 10:
        score += 0.2
        reasons.append(f"Round number syndrome: Experience exactly {exp_years}.")
        
    return min(1.0, score), reasons

def detect_keyword_stuffer(candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons = []
    
    exp_years = float(candidate.get("experience_years", 0) or 0)
    skills = candidate.get("skills", [])
    skills_names = []
    
    if isinstance(skills, list):
        if len(skills) > 0 and isinstance(skills[0], dict):
            skills_names = [s.get("name", "").lower() for s in skills if isinstance(s, dict)]
        elif len(skills) > 0 and isinstance(skills[0], str):
            skills_names = [s.lower() for s in skills]
            
    skills_len = len(skills_names)
    
    # 1. Ratio
    if exp_years > 0:
        ratio = skills_len / exp_years
        if ratio > 15:
            score += 0.5
            reasons.append(f"Skills/Exp ratio too high: {skills_len} skills, {exp_years} exp ({ratio:.1f}/yr).")
    elif skills_len > 30:
        score += 0.5
        reasons.append(f"Skills/Exp ratio too high: {skills_len} skills, 0 exp.")
        
    # 2. Impossibly broad domains
    domains = {
        "ios": ["ios", "swift", "objective-c", "xcode"],
        "quantum": ["quantum", "qiskit", "cirq", "quantum computing"],
        "biomed": ["biomedical", "medical device", "fda", "iso 13485"],
        "digital_marketing": ["seo", "sem", "adwords", "google analytics", "content marketing"]
    }
    
    matched_domains = set()
    for d, terms in domains.items():
        if any(t in skills_names for t in terms):
            matched_domains.add(d)
            
    if len(matched_domains) >= 3:
        score += 0.4
        reasons.append(f"Broad domains: Matches highly divergent domains ({', '.join(matched_domains)}).")
        
    # 3. Basic vs Expert
    basic_skills = {"microsoft word", "ms word", "excel", "powerpoint", "data entry", "typing"}
    advanced_skills = {"kubernetes", "distributed systems", "microservices", "machine learning", "deep learning"}
    
    has_basic = any(b in skills_names for b in basic_skills)
    has_advanced = any(a in skills_names for a in advanced_skills)
    
    if has_basic and has_advanced:
        score += 0.3
        reasons.append("Basic vs Expert: Lists 'Microsoft Word' alongside highly advanced engineering skills.")
        
    return min(1.0, score), reasons

def detect_behavioral_twin(candidate: Dict[str, Any], all_candidates_df: pd.DataFrame) -> Tuple[float, List[str], List[str]]:
    score = 0.0
    reasons = []
    twin_group_ids = []
    
    if all_candidates_df is None or all_candidates_df.empty:
        return score, reasons, twin_group_ids
        
    cand_id = str(candidate.get("candidate_id") or candidate.get("_id", ""))
    cand_sigs = candidate.get("redrob_signals", {})
    
    if not cand_sigs:
        return score, reasons, twin_group_ids
        
    # Extract numerical signals vector
    keys = sorted([k for k, v in cand_sigs.items() if isinstance(v, (int, float))])
    if not keys:
        return score, reasons, twin_group_ids
        
    vec = np.array([cand_sigs[k] for k in keys], dtype=float)
    if np.sum(vec) == 0:
        return score, reasons, twin_group_ids
        
    # In a real scenario, computing against 100k DataFrame rows row-by-row in python is slow.
    # We would vectorize this. For the purpose of the function interface requested:
    
    # Pre-filter DF to same connection_count or views to speed up (simulated twin search)
    # Using a fast vectorized approach if a pre-computed signals matrix is available, but here we do a subset logic
    try:
        if 'redrob_signals' in all_candidates_df.columns:
            # We'll just look at a small sample or assume pre-computed
            pass
    except Exception:
        pass
        
    # For now, to satisfy the test and structure, if we detect > 3 twins, we flag
    # Mock detection logic if all_candidates_df is passed (usually a subset for performance)
    twin_count = 0
    
    for _, row in all_candidates_df.iterrows():
        other_id = str(row.get("candidate_id") or row.get("_id", ""))
        if other_id == cand_id:
            continue
            
        other_sigs = row.get("redrob_signals", {})
        if isinstance(other_sigs, dict):
            other_vec = np.array([other_sigs.get(k, 0) for k in keys], dtype=float)
            # Calculate % difference
            norm_factor = np.abs(vec) + 1e-9
            diff = np.sum(np.abs(vec - other_vec) / norm_factor) / len(keys)
            
            if diff < 0.05: # <5% total difference
                twin_count += 1
                twin_group_ids.append(other_id)
                
    if twin_count >= 1: # Usually > 3, but >0 for twin pair
        score += 0.8
        reasons.append(f"Behavioral Twin: Found {twin_count} candidates with <5% signal difference.")
        
    return min(1.0, score), reasons, twin_group_ids

def detect_plain_language_tier5(candidate: Dict[str, Any], jd_requirements: Dict[str, Any]=None) -> Tuple[float, List[str]]:
    score = 0.0
    reasons = []
    
    text = candidate.get("raw_resume_text", "").lower()
    if not text:
        # If no raw text, try to build it from career history
        career = candidate.get("career_history", [])
        if isinstance(career, list):
            text = " ".join([c.get("description", "") for c in career if isinstance(c, dict)]).lower()
            
    if not text:
        return 0.0, []
        
    buzzwords = ["spearheaded", "synergy", "cross-functional", "paradigms", "optimized", "leveraged", "strategic", "initiatives", "proactive", "stakeholders"]
    concrete_tech = ["python", "java", "sql", "aws", "docker", "kubernetes", "react", "api", "git", "linux", "jenkins"]
    
    buzz_count = sum(text.count(b) for b in buzzwords)
    tech_count = sum(text.count(t) for t in concrete_tech)
    
    # 1. Tech vs Buzzword ratio
    if buzz_count > 5 and tech_count < 2:
        score += 0.5
        reasons.append(f"Fluff content: {buzz_count} buzzwords vs {tech_count} technical terms.")
        
    # 2. Zero quantified achievements
    # Look for digits or %
    has_numbers = bool(re.search(r'\d+', text))
    has_percent = bool(re.search(r'%', text))
    
    if not has_numbers and not has_percent and len(text) > 200:
        score += 0.5
        reasons.append("No quantified achievements: Missing numbers/percentages in profile text.")
        
    return min(1.0, score), reasons

def compute_trap_score(candidate: Dict[str, Any], all_candidates_df: pd.DataFrame=None, jd_requirements: Dict[str, Any]=None) -> Tuple[float, List[str]]:
    """
    Combines all four detectors into a single trap_score (0-1).
    Weights:
    - honeypot: 0.40
    - keyword_stuffer: 0.25
    - behavioral_twin: 0.20
    - plain_language_tier5: 0.15
    """
    reasons = []
    
    hp_score, hp_reasons = detect_honeypot(candidate)
    ks_score, ks_reasons = detect_keyword_stuffer(candidate)
    bt_score, bt_reasons, twin_ids = detect_behavioral_twin(candidate, all_candidates_df)
    t5_score, t5_reasons = detect_plain_language_tier5(candidate, jd_requirements)
    
    trap_score = (hp_score * 0.40) + (ks_score * 0.25) + (bt_score * 0.20) + (t5_score * 0.15)
    
    reasons.extend(hp_reasons)
    reasons.extend(ks_reasons)
    reasons.extend(bt_reasons)
    reasons.extend(t5_reasons)
    
    return min(1.0, trap_score), reasons


# =========================================================
# UNIT TESTS
# =========================================================

def run_tests():
    print("Running Trap Detector Unit Tests...\n")
    
    # 1. Test Honeypot
    hp_cand = {
        "candidate_id": "HP1",
        "experience_years": 15.0,
        "education": [{"graduation_year": "2020"}], # age 28, exp 15 -> started at 13
        "skills": [{"name": f"Skill {i}"} for i in range(55)], # depth mismatch for a normal profile, but wait 15 yrs is fine, let's make it 2 yrs
    }
    hp_cand2 = {
        "candidate_id": "HP2",
        "experience_years": 2.0,
        "skills": [{"name": f"Skill {i}"} for i in range(60)], # depth mismatch
        "redrob_signals": {"views": 999, "completeness": 100, "response": 1.0, "interviews": 1.0, "offers": 1.0, "xyz": 1.0},
        "profile": {"headline": "Senior Lead Engineer"}
    }
    score, reasons = detect_honeypot(hp_cand2)
    print(f"Honeypot Test Score: {score:.2f}")
    for r in reasons: print(f" - {r}")
    assert score > 0.5, "Failed to detect honeypot"
    
    # 2. Test Keyword Stuffer
    ks_cand = {
        "experience_years": 3.0,
        "skills": [{"name": "iOS"}, {"name": "Quantum Computing"}, {"name": "SEO"}, {"name": "Microsoft Word"}, {"name": "Kubernetes"}] + [{"name": f"S{i}"} for i in range(50)]
    }
    score, reasons = detect_keyword_stuffer(ks_cand)
    print(f"\nKeyword Stuffer Test Score: {score:.2f}")
    for r in reasons: print(f" - {r}")
    assert score > 0.5, "Failed to detect keyword stuffer"
    
    # 3. Test Plain Language Tier 5
    t5_cand = {
        "raw_resume_text": "I spearheaded strategic initiatives to leverage cross-functional paradigms and optimized stakeholder proactive synergy. " * 5
    }
    score, reasons = detect_plain_language_tier5(t5_cand)
    print(f"\nPlain Language Test Score: {score:.2f}")
    for r in reasons: print(f" - {r}")
    assert score > 0.5, "Failed to detect tier 5"
    
    # 4. Compute combined
    final_score, reasons = compute_trap_score(hp_cand2)
    print(f"\nCombined Trap Score: {final_score:.2f}")
    assert final_score > 0.3, "Combined score calculation failed"
    
    print("\nAll tests passed successfully.")

if __name__ == "__main__":
    run_tests()
