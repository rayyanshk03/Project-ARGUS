import numpy as np
from typing import List, Tuple, Dict, Any
import numpy as np
from typing import List, Tuple, Dict, Any

def sigmoid(x: float) -> float:
    return 1 / (1 + np.exp(-x))

def _match_skill_list(target_skills: List[str], candidate_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Helper function to evaluate a specific list of target skills.
    Replaced heavy CrossEncoder with fast string matching to meet CPU constraint.
    Returns (normalized_score, matched_skills, missing_skills)
    """
    if not target_skills:
        return 1.0, [], []
        
    candidate_skills_lower = [str(s).lower() for s in (candidate_skills or [])]
    
    matched = []
    missing = []
    total_score = 0.0
    
    # Fast path: Substring matching (e.g. "react" inside "react.js")
    for req_skill in target_skills:
        req_lower = req_skill.lower()
        found = False
        
        for cand_skill in candidate_skills_lower:
            if req_lower in cand_skill or cand_skill in req_lower:
                found = True
                break
                
        if found:
            matched.append(req_skill)
            total_score += 1.0
        else:
            missing.append(req_skill)
        
    normalized_score = total_score / len(target_skills) if target_skills else 1.0
    return normalized_score, matched, missing

def skill_match_score(required_skills: List[str], nice_to_have_skills: List[str], candidate_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Evaluates how well a candidate's skills match the JD.
    Fast CPU-only matching (O(N) string search, no neural networks here).
    """
    req_score, req_matched, req_missing = _match_skill_list(required_skills, candidate_skills)
    nice_score, nice_matched, nice_missing = _match_skill_list(nice_to_have_skills, candidate_skills)
    
    if not required_skills and not nice_to_have_skills:
        return 1.0, [], []
        
    # Weight required skills at 80% and nice-to-have at 20%
    if not required_skills:
        final_score = nice_score
    elif not nice_to_have_skills:
        final_score = req_score
    else:
        final_score = (0.8 * req_score) + (0.2 * nice_score)
        
    all_matched = req_matched + nice_matched
    all_missing = req_missing + nice_missing
    
    return final_score, all_matched, all_missing


def experience_match_score(jd_min_years: float, candidate_years: float) -> float:
    """
    Calculates an experience match score.
    Overqualification yields a small capped bonus.
    Underqualification yields a linear penalty floored at 0.2.
    """
    if candidate_years is None:
        candidate_years = 0.0
    if jd_min_years is None:
        jd_min_years = 0.0
        
    try:
        candidate_years = float(candidate_years)
        jd_min_years = float(jd_min_years)
    except ValueError:
        candidate_years = 0.0
        
    if jd_min_years <= 0:
        return 1.0
        
    if candidate_years >= jd_min_years:
        # Small bonus for overqualification capped at 1.0. 
        # (Since it's a 0-1 scale, we cap strictly at 1.0 to avoid breaking down-stream weights)
        bonus = (candidate_years - jd_min_years) * 0.05
        return min(1.0, 0.95 + bonus) 
    else:
        # Linear penalty for being below requirement
        score = candidate_years / jd_min_years
        # Floor at 0.2 so they aren't zeroed out completely
        return max(0.2, score)


def education_match_score(jd_edu: str, candidate_edu_list: List[dict]) -> float:
    """
    1 if meets/exceeds requirement, 0.5 if close, 0.2 if not.
    """
    if not jd_edu:
        return 1.0
        
    jd_edu_lower = str(jd_edu).lower()
    
    degree_levels = {
        "phd": 4, "doctorate": 4,
        "master": 3, "ms": 3, "ma": 3,
        "bachelor": 2, "bs": 2, "ba": 2,
        "associate": 1,
        "high school": 0
    }
    
    jd_level = 0
    for kw, level in degree_levels.items():
        if kw in jd_edu_lower:
            jd_level = max(jd_level, level)
            
    if not candidate_edu_list:
        return 0.2
        
    cand_level = 0
    for edu in candidate_edu_list:
        deg = str(edu.get("degree", "")).lower()
        for kw, level in degree_levels.items():
            if kw in deg:
                cand_level = max(cand_level, level)
                
    if cand_level >= jd_level:
        return 1.0
    elif cand_level == jd_level - 1:
        return 0.5
    return 0.2


def build_ranking_features(jd_reqs: dict, semantic_score: float, candidate: dict) -> dict:
    """
    Build a feature matrix row for a (job, candidate) pair.
    """
    import sys
    import os
    # Ensure we can import behavior
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from behavior import predict_behavior_score
    
    req_skills = jd_reqs.get("required_skills", [])
    nice_skills = jd_reqs.get("nice_to_have_skills", [])
    jd_min_years = jd_reqs.get("min_experience_years", 0)
    jd_edu = jd_reqs.get("education_requirement")
    
    cand_skills = candidate.get("skills", [])
    cand_exp = candidate.get("experience_years", 0)
    cand_edu_list = candidate.get("education", [])
    
    skill_score, _, _ = skill_match_score(req_skills, nice_skills, cand_skills)
    exp_score = experience_match_score(jd_min_years, cand_exp)
    edu_score = education_match_score(jd_edu, cand_edu_list)
    
    certs = candidate.get("certifications", [])
    cert_count = len(certs) if isinstance(certs, list) else 0
    cert_score = min(1.0, cert_count / 3.0) 
    
    projs = candidate.get("projects", [])
    proj_count = len(projs) if isinstance(projs, list) else 0
    proj_score = min(1.0, proj_count / 5.0)
    
    cand_id = str(candidate.get("_id", candidate.get("candidate_id", "")))
    behavior_score = predict_behavior_score(cand_id) if cand_id else 0.5
    
    return {
        "candidate_id": cand_id,
        "semantic_score": float(semantic_score),
        "skill_match_score": float(skill_score),
        "experience_match_score": float(exp_score),
        "education_match_score": float(edu_score),
        "behavior_score": float(behavior_score),
        "certifications_count": float(cert_count),
        "certifications_score": float(cert_score),
        "projects_count": float(proj_count),
        "projects_score": float(proj_score)
    }


def generate_synthetic_ranking_labels(df) -> Any:
    """
    Generates a weak-supervision ground truth label using a weighted domain formula.
    
    NOTE ON LEARNING TO RANK:
    This lets the LightGBM Ranker (lambdarank) learn to approximate and refine this weighted heuristic.
    In a real production system, you would REPLACE these synthetic labels with real implicit/explicit 
    recruiter feedback (e.g., Shortlisted=1, Rejected=0, Hired=2). The LTR model would then learn 
    nuanced, non-linear interactions between features (e.g., high semantic score matters less if 
    behavior is zero) that a simple static weighted sum cannot capture.
    """
    final_score = (
        0.35 * df["semantic_score"] +
        0.20 * df["skill_match_score"] +
        0.15 * df["experience_match_score"] +
        0.10 * df["education_match_score"] +
        0.10 * df["behavior_score"] +
        0.05 * df["certifications_score"] +
        0.05 * df["projects_score"]
    )
    # LTR targets are usually integer relevance grades (e.g., 0 to 4)
    relevance_grade = (final_score * 4.0).round().astype(int)
    return relevance_grade.clip(lower=0, upper=4)


def train_ranker():
    import pandas as pd
    import lightgbm as lgb
    import os
    import pickle
    from parser import connect_db
    from embeddings import semantic_search
    from llm import understand_job_description
    from bson import ObjectId
    
    db = connect_db()
    candidates = list(db["candidates"].find())
    if not candidates:
        print("No candidates found.")
        return
        
    mock_jds = [
        "Senior Backend Engineer with Python and AWS",
        "Frontend React Developer 3 years experience",
        "Data Scientist Machine Learning PhD required",
        "DevOps Engineer Kubernetes Docker Docker-Compose"
    ]
    
    all_features = []
    groups = []
    
    print("Building synthetic LTR dataset...")
    for q_idx, query in enumerate(mock_jds):
        jd_reqs = understand_job_description(query)
        top_cands = semantic_search(query, top_k=20)
        
        group_size = 0
        for cid, sem_score in top_cands:
            cand_doc = db["candidates"].find_one({"_id": ObjectId(cid)})
            if cand_doc:
                feats = build_ranking_features(jd_reqs, sem_score, cand_doc)
                feats["job_id"] = q_idx
                all_features.append(feats)
                group_size += 1
                
        if group_size > 0:
            groups.append(group_size)
        
    if not all_features:
        print("No feature data generated.")
        return
        
    df = pd.DataFrame(all_features)
    y = generate_synthetic_ranking_labels(df)
    X = df.drop(columns=["candidate_id", "job_id"])
    
    print("Training LightGBM Ranker (LambdaRank)...")
    model = lgb.LGBMRanker(
        objective="lambdarank",
        metric="ndcg",
        n_estimators=100,
        learning_rate=0.05,
        verbosity=-1
    )
    
    model.fit(X, y, group=groups)
    
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    with open(os.path.join(models_dir, "lightgbm_ranker.pkl"), 'wb') as f:
        pickle.dump(model, f)
        
    print("Ranker trained and saved successfully.")


def rank_candidates(jd_requirements: dict, candidate_pool: List[Tuple[str, float]]) -> List[dict]:
    """
    Runs the full pipeline (semantic_search -> skill/experience/education/behavior scoring -> ranker.predict).
    Falls back gracefully to the plain weighted-sum formula if the trained ranker model file doesn't exist.
    """
    import os
    import pickle
    import pandas as pd
    from parser import connect_db
    from bson import ObjectId
    
    db = connect_db()
    results = []
    
    for cid, sem_score in candidate_pool:
        doc = db["candidates"].find_one({"_id": ObjectId(cid)})
        if not doc:
            continue
            
        feats = build_ranking_features(jd_requirements, sem_score, doc)
        
        # Attach raw doc fields for transparency in output
        feats["name"] = doc.get("name", "Unknown")
        feats["email"] = doc.get("email", "")
        results.append(feats)
        
    if not results:
        return []
        
    df = pd.DataFrame(results)
    
    # Fallback formula
    df["fallback_score"] = (
        0.35 * df["semantic_score"] +
        0.20 * df["skill_match_score"] +
        0.15 * df["experience_match_score"] +
        0.10 * df["education_match_score"] +
        0.10 * df["behavior_score"] +
        0.05 * df["certifications_score"] +
        0.05 * df["projects_score"]
    )
    
    model_path = os.path.join(os.path.dirname(__file__), "models", "lightgbm_ranker.pkl")
    used_model = False
    
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            X = df.drop(columns=["candidate_id", "name", "email", "fallback_score", "job_id", "final_score"], errors='ignore')
            df["final_score"] = model.predict(X)
            used_model = True
        except Exception as e:
            print(f"Failed to load ranker model: {e}")
            df["final_score"] = df["fallback_score"]
    else:
        df["final_score"] = df["fallback_score"]
        
    df = df.sort_values(by="final_score", ascending=False)
    out = df.to_dict(orient="records")
    
    for row in out:
        row["used_ml_ranker"] = used_model
        
    return out


if __name__ == "__main__":
    print("=== Testing CrossEncoder Reranker Module ===")
    jd_reqs = ["Python", "FastAPI", "Docker"]
    nice_to_have = ["AWS", "Kubernetes"]
    jd_min_years = 5
    
    # 5 Sample Candidates
    test_candidates = [
        {"name": "Alice", "skills": ["Python", "Flask", "Docker", "AWS"], "exp": 4},
        {"name": "Bob", "skills": ["Java", "Spring", "Kubernetes"], "exp": 2},
        {"name": "Charlie", "skills": ["python", "FastAPI", "docker", "aws", "kubernetes"], "exp": 6},
        {"name": "Diana", "skills": ["Django", "Containerization", "GCP"], "exp": 5},
        {"name": "Eve", "skills": ["Node.js", "Express", "Docker"], "exp": 3}
    ]
    
    print(f"JD Required Skills : {jd_reqs}")
    print(f"JD Nice-to-have    : {nice_to_have}")
    print(f"Min Experience     : {jd_min_years} years\n")
    
    for c in test_candidates:
        print(f"▶ Candidate: {c['name']} (Exp: {c['exp']} yrs)")
        print(f"  Skills: {c['skills']}")
        
        skill_score, matched, missing = skill_match_score(jd_reqs, nice_to_have, c["skills"])
        exp_score = experience_match_score(jd_min_years, c["exp"])
        
        print(f"  Matched: {matched}")
        print(f"  Missing: {missing}")
        print(f"  Skill Score : {skill_score:.2f} / 1.0")
        print(f"  Exp Score   : {exp_score:.2f} / 1.0\n")
