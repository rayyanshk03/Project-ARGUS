import os
import json
import time
import pandas as pd
from typing import Dict, Any, List, Tuple

# Local imports
from embeddings import semantic_search, build_index_if_missing, get_model
from trap_detector import compute_trap_score

try:
    from sentence_transformers import CrossEncoder
    CE_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "cross_encoder")
except ImportError:
    pass

def load_cross_encoder():
    print("Loading CrossEncoder for reranking...")
    model_name_or_path = CE_MODEL_PATH if os.path.exists(CE_MODEL_PATH) else 'cross-encoder/ms-marco-MiniLM-L-6-v2'
    return CrossEncoder(model_name_or_path)

def parse_jd(jd_path: str) -> Dict[str, Any]:
    """Basic extraction for the JD text to structured requirements without an LLM call (to save time)."""
    # In a real scenario, this might use a local lightweight NER model or regex.
    # For now, we mock the parsed representation based on keywords in the text.
    with open(jd_path, 'r', encoding='utf-8') as f:
        text = f.read().lower()
        
    reqs = {
        "role_title": "Software Engineer",
        "seniority_level": "Mid-Senior",
        "industry_domain": "Technology",
        "required_skills": [],
        "min_experience_years": 3.0
    }
    
    # Very basic regex/keyword extraction for the hackathon
    tech_keywords = ["python", "java", "react", "aws", "docker", "kubernetes", "fastapi", "sql", "node", "typescript"]
    reqs["required_skills"] = [k for k in tech_keywords if k in text]
    
    if "senior" in text or "lead" in text:
        reqs["min_experience_years"] = 5.0
        reqs["seniority_level"] = "Senior"
        
    return reqs

def load_candidates_streaming(candidates_path: str) -> List[Dict[str, Any]]:
    """Stream jsonl to avoid loading 465MB entirely into RAM at once, just keep what we need."""
    print("Streaming candidates...")
    candidates = []
    required_cols = ["candidate_id", "name", "experience_years", "skills", "redrob_signals", "raw_resume_text", "profile", "education", "career_history"]
    
    try:
        if candidates_path.endswith('.jsonl') or candidates_path.endswith('.gz'):
            import gzip
            open_func = gzip.open if candidates_path.endswith('.gz') else open
            mode = 'rt' if candidates_path.endswith('.gz') else 'r'
            with open_func(candidates_path, mode, encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if not line.strip(): continue
                    data = json.loads(line)
                    c_id = data.get("candidate_id") or str(data.get("_id", f"CAND_{i}"))
                    candidates.append({
                        "candidate_id": c_id,
                        "name": data.get("name", "Unknown"),
                        "experience_years": data.get("experience_years", 0),
                        "skills": data.get("skills", []),
                        "redrob_signals": data.get("redrob_signals", {}),
                        "raw_resume_text": data.get("raw_resume_text", ""),
                        "profile": data.get("profile", {}),
                        "education": data.get("education", []),
                        "career_history": data.get("career_history", [])
                    })
        else:
            with open(candidates_path, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
                for i, data in enumerate(data_list):
                    c_id = data.get("candidate_id") or str(data.get("_id", f"CAND_{i}"))
                    candidates.append({
                        "candidate_id": c_id,
                        "name": data.get("name", "Unknown"),
                        "experience_years": data.get("experience_years", 0),
                        "skills": data.get("skills", []),
                        "redrob_signals": data.get("redrob_signals", {}),
                        "raw_resume_text": data.get("raw_resume_text", ""),
                        "profile": data.get("profile", {}),
                        "education": data.get("education", []),
                        "career_history": data.get("career_history", [])
                    })
    except Exception as e:
        print(f"Error loading {candidates_path}: {e}")
        
    return candidates

def experience_score(candidate_experience_years: float, jd_min_years: float) -> float:
    exp = candidate_experience_years
    if exp >= jd_min_years * 1.5:
        return 0.9
    elif jd_min_years <= exp < jd_min_years * 1.5:
        return 1.0
    elif exp >= jd_min_years * 0.8:
        return 0.75
    elif exp >= jd_min_years * 0.5:
        return 0.50
    else:
        return 0.20

def compute_behavior_score(candidate: Dict[str, Any]) -> float:
    sigs = candidate.get("redrob_signals", {})
    if not sigs:
        return 0.5
    # Aggregate specific positive signals
    score = 0.0
    
    # Recency / Responsiveness
    rr = sigs.get("recruiter_response_rate", 0.5)
    score += rr * 0.4
    
    # Activity
    views = min(1.0, sigs.get("profile_views_received_30d", 0) / 100.0)
    score += views * 0.3
    
    # Quality / GitHub
    gh = min(1.0, max(0.0, sigs.get("github_activity_score", 0) / 50.0))
    score += gh * 0.3
    
    return min(1.0, score)

def compute_education_score(candidate: Dict[str, Any]) -> float:
    # Simplified logic for hackathon
    edu = candidate.get("education", [])
    if edu:
        return 1.0
    return 0.5

def compute_completeness_bonus(candidate: Dict[str, Any]) -> float:
    sigs = candidate.get("redrob_signals", {})
    comp = sigs.get("profile_completeness_score", 50.0)
    return min(1.0, comp / 100.0)

def extract_skills_list(candidate: Dict[str, Any]) -> List[str]:
    skills = candidate.get("skills", [])
    if isinstance(skills, list) and len(skills) > 0 and isinstance(skills[0], dict):
        return [s.get("name", "").lower() for s in skills]
    elif isinstance(skills, list):
        return [str(s).lower() for s in skills]
    return []

def build_reasoning(candidate: Dict[str, Any], scores: Dict[str, float], jd_requirements: Dict[str, Any]) -> str:
    exp_years = candidate.get("experience_years", 0)
    
    req_skills = [s.lower() for s in jd_requirements.get("required_skills", [])]
    cand_skills = extract_skills_list(candidate)
    
    matched = list(set(cand_skills).intersection(set(req_skills)))
    matched_count = len(matched)
    req_count = len(req_skills) if req_skills else 1
    
    skill_coverage = matched_count / req_count
    
    top_2_matched = ", ".join(matched[:2]) if len(matched) >= 2 else (", ".join(matched) if matched else "key skills")
    top_domain = jd_requirements.get("industry_domain", "the industry")
    
    missing = list(set(req_skills) - set(cand_skills))
    missing_skill = missing[0] if missing else "required areas"
    top_skill = cand_skills[0] if cand_skills else "general tech"
    
    sigs = candidate.get("redrob_signals", {})
    views = sigs.get("profile_views_received_30d", 0)
    recency_note = ", recently active" if views > 10 else ""
    gap_note = f", missing {missing_skill}" if missing else ""
    
    if skill_coverage >= 0.8:
        return f"Directly matches {matched_count} of {req_count} required skills including {top_2_matched}, {exp_years} years experience{recency_note}."
    elif skill_coverage >= 0.5:
        return f"Strong semantic alignment in {top_domain}, covers {matched_count} required skills, {exp_years} years experience{gap_note}."
    else:
        return f"Relevant background in {top_domain} with transferable skills in {top_skill}, may require upskilling in {missing_skill}."

def run_ranking(jd_path: str, candidates_path: str, output_path: str):
    t0 = time.time()
    
    # 1. Parse JD
    t_start = time.time()
    jd_reqs = parse_jd(jd_path)
    print(f"1. Parsed JD in {time.time()-t_start:.2f}s")
    
    # 2. Load Candidates
    t_start = time.time()
    candidates = load_candidates_streaming(candidates_path)
    cand_dict = {c["candidate_id"]: c for c in candidates}
    print(f"2. Loaded {len(candidates)} candidates in {time.time()-t_start:.2f}s")
    
    # 3. Compute Trap Scores
    t_start = time.time()
    # We do this for all candidates first to find twin groups across the whole dataset
    # In practice for 100k, building a DataFrame takes memory. We'll pass a subset to detect twins or rely on fast iteration
    trap_results = {}
    
    # Minimal DF for behavioral twin detection to save memory
    twin_df_data = []
    for c in candidates:
        if "redrob_signals" in c:
            row = {"candidate_id": c["candidate_id"]}
            row.update({k: v for k, v in c["redrob_signals"].items() if isinstance(v, (int, float))})
            twin_df_data.append(row)
    twin_df = pd.DataFrame(twin_df_data)
    
    for c in candidates:
        cid = c["candidate_id"]
        t_score, t_reasons = compute_trap_score(c, all_candidates_df=twin_df, jd_requirements=jd_reqs)
        trap_results[cid] = t_score
    print(f"3. Trap scoring complete in {time.time()-t_start:.2f}s")
    
    # 4 & 5. FAISS Search
    t_start = time.time()
    with open(jd_path, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    build_index_if_missing(candidates_path) # Embeds if missing
    top_500_faiss = semantic_search(jd_reqs, top_k=500)
    print(f"4 & 5. FAISS retrieval (top 500) in {time.time()-t_start:.2f}s")
    
    # 6. Cross-Encoder Reranking
    t_start = time.time()
    cross_encoder = load_cross_encoder()
    
    # Build pairs
    pairs = []
    for cid, sem_score in top_500_faiss:
        c = cand_dict[cid]
        c_text = c.get("raw_resume_text", "")
        pairs.append([jd_text[:1000], c_text[:1000]]) # Truncate for cross encoder limits
        
    ce_scores = cross_encoder.predict(pairs)
    # Normalize cross encoder scores to 0-1
    ce_min, ce_max = ce_scores.min(), ce_scores.max()
    if ce_max > ce_min:
        ce_scores = (ce_scores - ce_min) / (ce_max - ce_min)
    else:
        ce_scores = [0.5] * len(pairs)
    print(f"6. Cross-Encoder reranking in {time.time()-t_start:.2f}s")
    
    # 7 & 8 & 9. Final Scoring & Penalties
    t_start = time.time()
    req_skills = [s.lower() for s in jd_reqs.get("required_skills", [])]
    jd_min_years = jd_reqs.get("min_experience_years", 0)
    
    final_candidates = []
    
    for i, (cid, sem_score) in enumerate(top_500_faiss):
        c = cand_dict[cid]
        
        # Skill Match Score
        cand_skills = extract_skills_list(c)
        matched = len(set(cand_skills).intersection(set(req_skills)))
        coverage = matched / max(1, len(req_skills))
        ce_score = ce_scores[i]
        skill_match_score = (0.6 * coverage) + (0.4 * ce_score)
        
        # Other scores
        exp_score = experience_score(float(c.get("experience_years", 0) or 0), jd_min_years)
        beh_score = compute_behavior_score(c)
        edu_score = compute_education_score(c)
        comp_bonus = compute_completeness_bonus(c)
        
        base_score = (
            0.35 * sem_score +
            0.25 * skill_match_score +
            0.15 * exp_score +
            0.15 * beh_score +
            0.05 * edu_score +
            0.05 * comp_bonus
        )
        
        # Apply trap penalty
        trap_score = trap_results.get(cid, 0)
        multiplier = 1.0
        if trap_score > 0.65:
            multiplier = 0.2
        elif trap_score >= 0.40:
            multiplier = 0.6
            
        final_score = base_score * multiplier
        
        scores_dict = {
            "semantic": sem_score, "skill_match": skill_match_score, 
            "exp": exp_score, "beh": beh_score, "trap": trap_score
        }
        
        reasoning = build_reasoning(c, scores_dict, jd_reqs)
        
        final_candidates.append({
            "candidate_id": cid,
            "final_score": final_score,
            "trap_score": trap_score,
            "reasoning": reasoning,
            "twin_group_id": None # Populated in deduplication if needed
        })
        
    print(f"7-9. Final Scoring & Penalties in {time.time()-t_start:.2f}s")
    
    # 10. Deduplicate Behavioral Twins
    # Since trap_detector identifies twins but returns it as a list of twin IDs per candidate, 
    # we can do a simple graph pass or just a greedy deduplication
    t_start = time.time()
    # Sort by final score first
    final_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    
    seen_twins = set()
    deduped = []
    
    for c_obj in final_candidates:
        cid = c_obj["candidate_id"]
        # If this candidate is known to be in a twin group that we already selected a rep for, skip
        if cid in seen_twins:
            continue
            
        # Get twin ids for this candidate (we recompute fast here or cache from step 3)
        # Assuming we cached from step 3, but let's just use the score sort. 
        # For full hackathon, we would read twin_ids returned from compute_trap_score
        # For now, we just add this candidate to deduped
        deduped.append(c_obj)
        
        # We would mark their twins as seen
        # e.g., seen_twins.update(c_obj["twin_ids"])
    print(f"10. Twin Deduplication in {time.time()-t_start:.2f}s")
    
    # 11. Top 100
    top_100 = deduped[:100]
    
    # 13. Export CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    records = []
    for i, c in enumerate(top_100):
        records.append({
            "rank": i + 1,
            "candidate_id": c["candidate_id"],
            "score": round(c["final_score"], 4),
            "reasoning": c["reasoning"]
        })
        
    df_out = pd.DataFrame(records)
    df_out.to_csv(output_path, index=False)
    
    # Assertions
    assert len(df_out) == 100, f"Output length {len(df_out)} != 100. Dataset might be too small!"
    assert len(df_out["candidate_id"].unique()) == 100, "Duplicate candidate IDs found in output!"
    
    print(f"\n✅ Pipeline Complete! Output saved to {output_path}")
    print(f"⏱️  Total Time Taken: {time.time()-t0:.2f}s")

if __name__ == "__main__":
    # Example local run
    JD_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "jd.txt")
    # For testing, we might want to use sample_candidates since full 100k doesn't exist locally here.
    CAND_PATH = os.environ.get("ACTIVE_CANDIDATES_PATH", "/Users/rayyanshaikh/Desktop/India_runs_data_and_ai_challenge/sample_candidates.json")
    OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "submission.csv")
    
    if os.path.exists(JD_PATH) and os.path.exists(CAND_PATH):
        try:
            run_ranking(JD_PATH, CAND_PATH, OUT_PATH)
        except Exception as e:
            print(f"Error during ranking: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Please ensure jd.txt and candidates data paths are valid before running.")

def rank_for_ui(jd_text: str) -> List[Dict[str, Any]]:
    import os
    from llm import understand_job_description
    
    # 1. Parse JD using existing logic
    jd_reqs = understand_job_description(jd_text)
    
    # 2. Load Candidates from JSON
    CAND_PATH = os.environ.get("ACTIVE_CANDIDATES_PATH", "/Users/rayyanshaikh/Desktop/India_runs_data_and_ai_challenge/sample_candidates.json")
    candidates = load_candidates_streaming(CAND_PATH)
    cand_dict = {c["candidate_id"]: c for c in candidates}
    
    # 3. FAISS Search
    build_index_if_missing(CAND_PATH)
    top_500_faiss = semantic_search(jd_reqs, top_k=min(100, len(candidates)))
    
    # 4. Cross Encoder
    cross_encoder = load_cross_encoder()
    pairs = []
    valid_faiss = []
    for cid, sem_score in top_500_faiss:
        c = cand_dict.get(cid)
        if not c: continue
        c_text = c.get("raw_resume_text", "")
        pairs.append([jd_text[:1000], c_text[:1000]])
        valid_faiss.append((cid, sem_score))
        
    ce_scores = cross_encoder.predict(pairs) if pairs else []
    if len(ce_scores) > 0:
        ce_min, ce_max = ce_scores.min(), ce_scores.max()
        if ce_max > ce_min:
            ce_scores = (ce_scores - ce_min) / (ce_max - ce_min)
        else:
            ce_scores = [0.5] * len(pairs)
            
    # Final Scoring
    req_skills = [s.lower() for s in jd_reqs.get("required_skills", [])]
    jd_min_years = jd_reqs.get("min_experience_years", 0)
    
    final_candidates = []
    for i, (cid, sem_score) in enumerate(valid_faiss):
        c = cand_dict[cid]
        c["candidate_id"] = cid
        
        prof = c.get("profile", {})
        c["title"] = prof.get("headline", "Candidate")
        c["location"] = prof.get("location", "Remote")
        
        career = c.get("career_history", [])
        if isinstance(career, list) and len(career) > 0 and isinstance(career[0], dict):
            c["company"] = career[0].get("company", "Unknown")
            c["title"] = career[0].get("title", c["title"])
        else:
            c["company"] = "Unknown"
            
        cand_skills = extract_skills_list(c)
        matched = len(set(cand_skills).intersection(set(req_skills)))
        coverage = matched / max(1, len(req_skills))
        ce_score = ce_scores[i]
        skill_match_score = (0.6 * coverage) + (0.4 * ce_score)
        
        exp_score = experience_score(float(c.get("experience_years", 0) or 0), jd_min_years)
        beh_score = compute_behavior_score(c)
        edu_score = compute_education_score(c)
        comp_bonus = compute_completeness_bonus(c)
        
        base_score = (
            0.35 * sem_score +
            0.25 * skill_match_score +
            0.15 * exp_score +
            0.15 * beh_score +
            0.05 * edu_score +
            0.05 * comp_bonus
        )
        
        trap_score, _ = compute_trap_score(c, all_candidates_df=None, jd_requirements=jd_reqs)
        multiplier = 1.0
        if trap_score > 0.65: multiplier = 0.2
        elif trap_score >= 0.40: multiplier = 0.6
            
        final_score = base_score * multiplier
        
        scores_dict = {
            "semantic": sem_score, "skill_match": skill_match_score, 
            "exp": exp_score, "beh": beh_score, "trap": trap_score
        }
        
        c["semantic_score"] = sem_score
        c["skill_match_score"] = skill_match_score
        c["experience_match_score"] = exp_score
        c["behavior_score"] = beh_score
        c["final_score"] = final_score
        c["trap_score"] = trap_score
        c["explanation"] = build_reasoning(c, scores_dict, jd_reqs)
        
        final_candidates.append(c)
        
    final_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    return final_candidates[:100]


def rank_candidates(jd_reqs: Dict[str, Any], pool: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
    """
    Called by api.py for the UI.
    pool is a list of (candidate_id, semantic_score).
    We fetch candidates from MongoDB, run the new scoring logic, and return.
    """
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from parser import connect_db
    from bson import ObjectId
    
    db = connect_db()
    cids = [ObjectId(cid) for cid, score in pool if len(cid) == 24]
    
    # Fetch docs
    docs = list(db["candidates"].find({"_id": {"$in": cids}}))
    cand_dict = {str(d["_id"]): d for d in docs}
    
    cross_encoder = load_cross_encoder()
    
    # Build pairs
    pairs = []
    valid_pool = []
    
    jd_text = " ".join(jd_reqs.get("required_skills", []))
    if jd_reqs.get("role_title"):
        jd_text = jd_reqs["role_title"] + " " + jd_text
        
    for cid, sem_score in pool:
        c = cand_dict.get(cid)
        if not c: continue
        c_text = c.get("raw_resume_text", "")
        pairs.append([jd_text[:1000], c_text[:1000]])
        valid_pool.append((cid, sem_score))
        
    ce_scores = cross_encoder.predict(pairs) if pairs else []
    if len(ce_scores) > 0:
        ce_min, ce_max = ce_scores.min(), ce_scores.max()
        if ce_max > ce_min:
            ce_scores = (ce_scores - ce_min) / (ce_max - ce_min)
        else:
            ce_scores = [0.5] * len(pairs)
            
    req_skills = [s.lower() for s in jd_reqs.get("required_skills", [])]
    jd_min_years = jd_reqs.get("min_experience_years", 0)
    
    final_candidates = []
    
    for i, (cid, sem_score) in enumerate(valid_pool):
        c = cand_dict[cid]
        c["candidate_id"] = cid
        
        # Populate for frontend
        prof = c.get("profile", {})
        c["title"] = prof.get("headline", "Candidate")
        c["location"] = prof.get("location", "Remote")
        
        career = c.get("career_history", [])
        if isinstance(career, list) and len(career) > 0 and isinstance(career[0], dict):
            c["company"] = career[0].get("company", "Unknown")
            c["title"] = career[0].get("title", c["title"])
        else:
            c["company"] = "Unknown"
            
        cand_skills = extract_skills_list(c)
        matched = len(set(cand_skills).intersection(set(req_skills)))
        coverage = matched / max(1, len(req_skills))
        ce_score = ce_scores[i]
        skill_match_score = (0.6 * coverage) + (0.4 * ce_score)
        
        exp_score = experience_score(float(c.get("experience_years", 0) or 0), jd_min_years)
        beh_score = compute_behavior_score(c)
        edu_score = compute_education_score(c)
        comp_bonus = compute_completeness_bonus(c)
        
        base_score = (
            0.35 * sem_score +
            0.25 * skill_match_score +
            0.15 * exp_score +
            0.15 * beh_score +
            0.05 * edu_score +
            0.05 * comp_bonus
        )
        
        trap_score, _ = compute_trap_score(c, all_candidates_df=None, jd_requirements=jd_reqs)
        multiplier = 1.0
        if trap_score > 0.65: multiplier = 0.2
        elif trap_score >= 0.40: multiplier = 0.6
            
        final_score = base_score * multiplier
        
        scores_dict = {
            "semantic": sem_score, "skill_match": skill_match_score, 
            "exp": exp_score, "beh": beh_score, "trap": trap_score
        }
        
        c["semantic_score"] = sem_score
        c["skill_match_score"] = skill_match_score
        c["experience_match_score"] = exp_score
        c["behavior_score"] = beh_score
        c["final_score"] = final_score
        c["trap_score"] = trap_score
        c["explanation"] = build_reasoning(c, scores_dict, jd_reqs)
        
        final_candidates.append(c)
        
    final_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    return final_candidates

