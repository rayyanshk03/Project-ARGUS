
def rank_candidates(jd_reqs: Dict[str, Any], pool: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
    """
    Called by api.py for the UI.
    pool is a list of (candidate_id, semantic_score).
    We fetch candidates from MongoDB, run the new scoring logic, and return.
    """
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from parser import connect_db
    
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
        
        # UI doesn't pass trap df for now, so we compute single
        trap_score, _ = compute_trap_score(c, all_candidates_df=None, jd_requirements=jd_reqs)
        multiplier = 1.0
        if trap_score > 0.65: multiplier = 0.2
        elif trap_score >= 0.40: multiplier = 0.6
            
        final_score = base_score * multiplier
        
        # Build explanation string
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
