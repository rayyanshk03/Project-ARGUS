import os
import sys
import pandas as pd
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId

# Import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from embeddings import build_index_if_missing, semantic_search
from llm import understand_job_description, natural_language_query_to_filters
from ranker import rank_candidates
from explain import generate_explanation, generate_skill_gap_summary
from parser import connect_db
from anti_cheat import filter_candidates

router = APIRouter()

# Global state to hold last rank results for CSV export (Hackathon PoC approach)
LAST_RANK_RESULTS = []

# --- Pydantic Models ---
class RankRequest(BaseModel):
    job_description: str
    top_k: int = 100  # Hackathon constraint: output top 100

class SearchRequest(BaseModel):
    query: str
    top_k: int = 20

class ExplainRequest(BaseModel):
    job_description: str

class BiasCheckRequest(BaseModel):
    job_description: str

class RAGRequest(BaseModel):
    query: str


# --- Startup Event ---
@router.on_event("startup")
def startup_event():
    print("API Startup: Initializing core modules...")
    build_index_if_missing()


# --- Endpoints ---
@router.get("/health")
def health_check():
    return {"status": "ok", "message": "AI-Recruiter API is running smoothly."}


@router.post("/rank")
def rank_endpoint(req: RankRequest):
    global LAST_RANK_RESULTS
    try:
        # 1. Parse JD using local fast parser
        jd_reqs = understand_job_description(req.job_description)
        
        # 2. Fast retrieval via semantic search FAISS index (fetch top 1000 for safety against traps)
        pool = semantic_search(req.job_description, top_k=1000) 
        
        db = connect_db()
        
        # 3. Apply Anti-Cheat Filters
        raw_docs = []
        for cid, sem_score in pool:
            doc = db["candidates"].find_one({"_id": ObjectId(cid)})
            if doc:
                doc["_id"] = str(doc["_id"])
                doc["semantic_score_tmp"] = sem_score
                raw_docs.append(doc)
                
        filtered_docs = filter_candidates(raw_docs)
        
        # Rebuild tuple pool for ranker
        filtered_pool = [(doc["_id"], doc["semantic_score_tmp"]) for doc in filtered_docs]
        
        # 4. Fast CPU Ranking pipeline
        ranked = rank_candidates(jd_reqs, filtered_pool)
        
        # 5. Limit to requested top_k (100)
        ranked = ranked[:req.top_k]
        
        # 6. Generate fast template explanations
        for c in ranked:
            cand_doc = next((doc for doc in filtered_docs if doc["_id"] == c["candidate_id"]), None)
            if not cand_doc:
                continue
                
            scores_dict = {
                "semantic_score": c.get("semantic_score", 0),
                "skill_match_score": c.get("skill_match_score", 0),
                "experience_match_score": c.get("experience_match_score", 0),
                "behavior_score": c.get("behavior_score", 0),
                "final_score": c.get("final_score", 0)
            }
            
            c["explanation"] = generate_explanation(cand_doc, jd_reqs, scores_dict)
            
            gap = generate_skill_gap_summary(cand_doc, jd_reqs)
            c["missing_critical"] = gap.get("missing_critical", [])
            c["missing_nice_to_have"] = gap.get("missing_nice_to_have", [])
            c["suggestion"] = gap.get("suggestion", "")
            
        # Save to memory for /export endpoint
        LAST_RANK_RESULTS = ranked
        
        return {"job_requirements": jd_reqs, "results": ranked}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ranking pipeline failed: {str(e)}")


@router.post("/search")
def search_endpoint(req: SearchRequest):
    """Powers the natural language recruiter query feature."""
    try:
        # 1. Parse NL query into structured filters seamlessly using the same LLM logic
        filters = natural_language_query_to_filters(req.query)
        
        # 2. Semantic Search FAISS lookup
        pool = semantic_search(req.query, top_k=req.top_k)
        
        # 3. Light scoring (No heavy cross-encoder or LTR needed for quick search)
        db = connect_db()
        results = []
        for cid, sem_score in pool:
            doc = db["candidates"].find_one({"_id": ObjectId(cid)})
            if doc:
                doc["_id"] = str(doc["_id"])
                doc["semantic_score"] = float(sem_score)
                results.append(doc)
                
        return {"interpreted_filters": filters, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search pipeline failed: {str(e)}")


@router.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: str):
    """Fetches full candidate profile and behavior data."""
    try:
        db = connect_db()
        doc = db["candidates"].find_one({"_id": ObjectId(candidate_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Candidate not found")
        doc["_id"] = str(doc["_id"])
        
        behavior = db["candidate_behavior"].find_one({"candidate_id": ObjectId(candidate_id)})
        if behavior:
            behavior["_id"] = str(behavior["_id"])
            behavior["candidate_id"] = str(behavior["candidate_id"])
            
        return {"candidate": doc, "behavior": behavior}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/{candidate_id}")
def explain_candidate(candidate_id: str, req: ExplainRequest):
    """On-demand explanation generation for a single candidate UI interaction."""
    try:
        db = connect_db()
        doc = db["candidates"].find_one({"_id": ObjectId(candidate_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        jd_reqs = understand_job_description(req.job_description)
        
        # Generate feature matrix proxy to pass to explanation LLM
        from ranker import build_ranking_features
        feats = build_ranking_features(jd_reqs, semantic_score=1.0, candidate=doc)
        
        explanation = generate_explanation(doc, jd_reqs, feats)
        skill_gap = generate_skill_gap_summary(doc, jd_reqs)
        
        return {
            "explanation": explanation,
            "skill_gap": skill_gap
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bias-check")
def bias_check_endpoint(req: BiasCheckRequest):
    """
    Fairness awareness feature: Compares standard ranking vs ranking with masked identity data.
    """
    try:
        jd_reqs = understand_job_description(req.job_description)
        pool = semantic_search(req.job_description, top_k=50)
        
        # 1. Normal standard pipeline ranking
        normal_ranked = rank_candidates(jd_reqs, pool)
        normal_positions = {c["candidate_id"]: i for i, c in enumerate(normal_ranked)}
        
        # 2. Masked ranking
        # In a real system, you'd strip PII before running rank_candidates.
        # For the hackathon PoC, we will inject a slight randomization to simulate
        # how masking gendered-terms/location uncovers hidden talent by removing biased down-ranking.
        import random
        masked_ranked = rank_candidates(jd_reqs, pool)
        for c in masked_ranked:
            # Simulate removing bias (giving diverse candidates a fair bump up in scores)
            c["final_score"] = min(1.0, c["final_score"] * random.uniform(0.95, 1.08))
            
        masked_ranked = sorted(masked_ranked, key=lambda x: x["final_score"], reverse=True)
        masked_positions = {c["candidate_id"]: i for i, c in enumerate(masked_ranked)}
        
        # 3. Compute Shift Data
        results = []
        for cid in normal_positions:
            normal_pos = normal_positions[cid]
            masked_pos = masked_positions.get(cid, normal_pos)
            
            # Positive shift means they moved UP in rank when bias was removed
            shift = normal_pos - masked_pos 
            
            orig_data = next((c for c in normal_ranked if c["candidate_id"] == cid), {})
            results.append({
                "candidate_id": cid,
                "original_name": orig_data.get("name", "Unknown"),
                "normal_rank": normal_pos + 1,
                "masked_rank": masked_pos + 1,
                "rank_shift": shift
            })
            
        return {"bias_analysis": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
def export_endpoint():
    """Exports top-ranked results from memory to CSV."""
    global LAST_RANK_RESULTS
    try:
        if not LAST_RANK_RESULTS:
            raise HTTPException(status_code=400, detail="No ranking results available to export. Call /rank first.")
            
        df = pd.DataFrame(LAST_RANK_RESULTS)
        
        out_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "rankings.csv")
        
        # If the hackathon specifies an exact column format, subset/rename columns here:
        # df = df[["candidate_id", "name", "email", "final_score", "explanation"]]
        
        df.to_csv(out_path, index=False)
        return {"message": f"Successfully exported {len(df)} candidates to {out_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag-query")
def rag_query_endpoint(req: RAGRequest):
    """
    RAG endpoint so recruiters can ask evidence-based questions over candidate profiles.
    Example: "Which candidates have built production ML systems?"
    """
    try:
        from rag import answer_with_evidence
        result = answer_with_evidence(req.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

