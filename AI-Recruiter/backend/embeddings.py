import os
import json
import time
import numpy as np
import faiss
from typing import List, Tuple, Dict, Any
from sentence_transformers import SentenceTransformer

# Directories and paths
VECTORS_DIR = os.path.join(os.path.dirname(__file__), "vectors")
INDEX_PATH = os.path.join(VECTORS_DIR, "faiss.index")
MAPPING_PATH = os.path.join(VECTORS_DIR, "id_mapping.json")
NPY_PATH = os.path.join(VECTORS_DIR, "embeddings.npy")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "minilm")

_model = None

def get_model():
    """Load the pre-downloaded MiniLM model from disk."""
    global _model
    if _model is None:
        print(f"Loading local embedding model from {MODEL_PATH} ...")
        t0 = time.time()
        # Fallback to HF string if local path doesn't exist yet (for development)
        model_name_or_path = MODEL_PATH if os.path.exists(MODEL_PATH) else 'all-MiniLM-L6-v2'
        _model = SentenceTransformer(model_name_or_path)
        print(f"Model loaded in {time.time() - t0:.2f}s")
    return _model

def truncate_middle(text: str, max_chars: int = 1200) -> str:
    """
    Truncates text from the middle to preserve both early career (end of text) 
    and recent experience (start of text).
    MiniLM max tokens is 256, which roughly corresponds to ~1200 characters.
    """
    if len(text) <= max_chars:
        return text
    
    half = (max_chars - 10) // 2
    return text[:half] + " ... " + text[-half:]

def build_candidate_text(candidate: Dict[str, Any]) -> str:
    """
    Constructs a weighted text blob for semantic embedding.
    - Skills: 3x
    - Titles/Companies: 1x
    - Experience summary: 1x
    - Education: 1x
    - No redrob_signals (behavioral, not semantic)
    """
    parts = []
    
    # 1. Experience & Seniority
    exp_years = float(candidate.get("experience_years", 0) or 0)
    profile = candidate.get("profile", {})
    headline = profile.get("headline", "")
    parts.append(f"{exp_years} years experience. {headline}")
    
    # 2. Skills (Weight x3)
    skills = candidate.get("skills", [])
    skill_names = []
    if isinstance(skills, list) and len(skills) > 0 and isinstance(skills[0], dict):
        skill_names = [s.get("name", "") for s in skills]
    elif isinstance(skills, list):
        skill_names = [str(s) for s in skills]
    
    skills_str = ", ".join(skill_names)
    parts.append(f"Skills: {skills_str} | {skills_str} | {skills_str}")
    
    # 3. Last 3 Job Titles + Companies (1x)
    career = candidate.get("career_history", [])
    if isinstance(career, list):
        recent_jobs = career[:3]
        jobs_str = " ".join([f"{j.get('title', '')} at {j.get('company', '')}" for j in recent_jobs if isinstance(j, dict)])
        parts.append(f"Experience: {jobs_str}")
        
    # 4. Education (1x)
    education = candidate.get("education", [])
    if isinstance(education, list) and len(education) > 0 and isinstance(education[0], dict):
        ed = education[0]
        parts.append(f"Education: {ed.get('degree', '')} in {ed.get('field_of_study', '')} at {ed.get('institution', '')}")
        
    full_text = " . ".join(parts)
    return truncate_middle(full_text)

def build_jd_text(jd_reqs: Dict[str, Any]) -> str:
    """
    Builds a rich query text from parsed JD requirements.
    Lists required skills multiple times and includes implicit keywords.
    """
    parts = []
    role = jd_reqs.get("role_title", "")
    level = jd_reqs.get("seniority_level", "")
    domain = jd_reqs.get("industry_domain", "")
    
    parts.append(f"Role: {level} {role} in {domain} domain.")
    
    req_skills = jd_reqs.get("required_skills", [])
    skills_str = ", ".join(req_skills)
    # Emphasize required skills
    parts.append(f"Must have strong expertise in: {skills_str} | {skills_str} | {skills_str}")
    
    # Implied skills hack
    implied = []
    skills_lower = [s.lower() for s in req_skills]
    if "fastapi" in skills_lower or "flask" in skills_lower or "django" in skills_lower:
        implied.append("Python API development backend REST services")
    if "react" in skills_lower or "angular" in skills_lower:
        implied.append("Frontend web development SPA UI UX")
    if "aws" in skills_lower or "gcp" in skills_lower:
        implied.append("Cloud infrastructure deployment devops")
        
    if implied:
        parts.append(f"Related areas: {' '.join(implied)}")
        
    nice_skills = jd_reqs.get("nice_to_have_skills", [])
    if nice_skills:
        parts.append(f"Nice to have: {', '.join(nice_skills)}")
        
    return " . ".join(parts)

def embed_text(text: str) -> np.ndarray:
    """Embeds a single string into a normalized 1D numpy array."""
    model = get_model()
    vec = model.encode([text], convert_to_numpy=True)[0]
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec

def generate_candidate_embeddings(candidates_path=None):
    """
    Optimized for 100k candidates on CPU in < 3 minutes.
    Reads candidates from JSONL, builds embeddings in batches, saves to .npy and FAISS.
    """
    print("\n--- Starting High-Speed Embedding Pipeline ---")
    t0 = time.time()
    
    if not candidates_path:
        # Default fallback for testing
        candidates_path = os.environ.get("ACTIVE_CANDIDATES_PATH", "/Users/rayyanshaikh/Desktop/India_runs_data_and_ai_challenge/sample_candidates.json")
        
    t_load = time.time()
    
    candidates = []
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
                        "profile": data.get("profile", {}),
                        "experience_years": data.get("experience_years", 0),
                        "skills": data.get("skills", []),
                        "career_history": data.get("career_history", []),
                        "education": data.get("education", [])
                    })
        else:
            with open(candidates_path, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
                for i, data in enumerate(data_list):
                    c_id = data.get("candidate_id") or str(data.get("_id", f"CAND_{i}"))
                    candidates.append({
                        "candidate_id": c_id,
                        "profile": data.get("profile", {}),
                        "experience_years": data.get("experience_years", 0),
                        "skills": data.get("skills", []),
                        "career_history": data.get("career_history", []),
                        "education": data.get("education", [])
                    })
    except Exception as e:
        print(f"Error loading {candidates_path}: {e}")
        
    print(f"[Timing] Data loading ({len(candidates)} records): {time.time() - t_load:.2f}s")
    
    if not candidates:
        print("No candidates found.")
        return
        
    os.makedirs(VECTORS_DIR, exist_ok=True)
    
    texts = [build_candidate_text(c) for c in candidates]
    ids = [str(c["candidate_id"]) for c in candidates]
    
    model = get_model()
    
    t_embed = time.time()
    if os.path.exists(NPY_PATH):
        print(f"Found existing embeddings cache at {NPY_PATH}. Loading...")
        embeddings = np.load(NPY_PATH)
        print(f"[Timing] Loaded cached embeddings: {time.time() - t_embed:.2f}s")
    else:
        print(f"Encoding {len(texts)} texts in batches of 512 on CPU...")
        # Optimal CPU batch size for minilm is ~512
        embeddings = model.encode(texts, batch_size=512, show_progress_bar=True, convert_to_numpy=True)
        print(f"[Timing] Encoding 100k candidates: {time.time() - t_embed:.2f}s")
        
        # Save cache
        np.save(NPY_PATH, embeddings)
        print(f"Saved {embeddings.shape} embeddings to {NPY_PATH}")

    t_faiss = time.time()
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]
    
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    
    faiss.write_index(index, INDEX_PATH)
    with open(MAPPING_PATH, 'w') as f:
        json.dump(ids, f)
        
    print(f"[Timing] FAISS Index build & save: {time.time() - t_faiss:.2f}s")
    print(f"✅ Total Embedding Pipeline Time: {time.time() - t0:.2f}s")

def load_index_and_mapping() -> Tuple[faiss.Index, List[str]]:
    if not os.path.exists(INDEX_PATH) or not os.path.exists(MAPPING_PATH):
        raise FileNotFoundError("FAISS index or mapping file not found. Build it first.")
        
    index = faiss.read_index(INDEX_PATH)
    with open(MAPPING_PATH, 'r') as f:
        id_mapping = json.load(f)
        
    return index, id_mapping

def semantic_search(jd_requirements: Dict[str, Any], top_k: int = 500) -> List[Tuple[str, float]]:
    """
    Embeds the JD, searches FAISS, returns list of (candidate_id, normalized_score).
    Searches top 500 candidates by default for the reranking stage.
    """
    t_search = time.time()
    try:
        index, id_mapping = load_index_and_mapping()
    except FileNotFoundError:
        print("Index not found during search. Attempting auto-build...")
        generate_candidate_embeddings()
        index, id_mapping = load_index_and_mapping()
        
    # Build robust JD query text
    if isinstance(jd_requirements, str):
        # Fallback if raw text is passed
        query_text = jd_requirements
    else:
        query_text = build_jd_text(jd_requirements)
        
    query_vec = embed_text(query_text)
    query_vec_2d = np.array([query_vec]).astype('float32')
    
    k = min(top_k, index.ntotal)
    if k == 0:
        return []
        
    D, I = index.search(query_vec_2d, k)
    
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < len(id_mapping) and idx != -1:
            norm_score = max(0.0, min(1.0, float(score)))
            results.append((id_mapping[idx], norm_score))
            
    # print(f"[Timing] FAISS Search ({k} results): {time.time() - t_search:.3f}s")
    return results

def build_index_if_missing(candidates_path=None):
    if not os.path.exists(INDEX_PATH) or not os.path.exists(MAPPING_PATH) or not os.path.exists(NPY_PATH):
        print("FAISS index/cache missing. Initiating build process...")
        generate_candidate_embeddings(candidates_path)
    else:
        print("FAISS index and cached embeddings found. Ready for search.")

if __name__ == "__main__":
    build_index_if_missing()
