import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from dotenv import load_dotenv

# Ensure we can import parser if run directly
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser import connect_db

load_dotenv()

# Configurable embedding model
# Options: "BAAI/bge-large-en-v1.5" or "all-mpnet-base-v2"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2")

# Directories and paths
VECTORS_DIR = os.path.join(os.path.dirname(__file__), "vectors")
INDEX_PATH = os.path.join(VECTORS_DIR, "faiss.index")
MAPPING_PATH = os.path.join(VECTORS_DIR, "id_mapping.json")

# Lazy loading for the SentenceTransformer model
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL} ...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def embed_text(text: str) -> np.ndarray:
    """
    Embeds a single string into a normalized 1D numpy array.
    """
    model = get_model()
    if not isinstance(text, str):
        text = str(text)
        
    vec = model.encode([text])[0]
    
    # L2 Normalize so that inner product equals cosine similarity
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
        
    return vec

def generate_candidate_embeddings():
    """
    Pulls candidates from MongoDB, embeds raw_resume_text, 
    and saves a normalized FAISS IndexFlatIP.
    """
    db = connect_db()
    collection = db["candidates"]
    
    # Fetch candidates that actually have resume text
    candidates = list(collection.find({"raw_resume_text": {"$exists": True, "$ne": ""}}))
    if not candidates:
        print("No candidates with raw_resume_text found in MongoDB.")
        return
        
    print(f"Generating embeddings for {len(candidates)} candidates using {EMBEDDING_MODEL}...")
    
    texts = [c["raw_resume_text"] for c in candidates]
    ids = [str(c["_id"]) for c in candidates]
    
    model = get_model()
    print("Encoding texts in batches. This may take a moment...")
    
    # sentence-transformers supports batch_size internally
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    
    # L2 Normalize all embeddings for IndexFlatIP (Inner Product) = Cosine Sim
    faiss.normalize_L2(embeddings)
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    
    os.makedirs(VECTORS_DIR, exist_ok=True)
    
    faiss.write_index(index, INDEX_PATH)
    with open(MAPPING_PATH, 'w') as f:
        json.dump(ids, f)
        
    print(f"✅ FAISS index built and saved! ({index.ntotal} vectors of dim {dim})")

def load_index_and_mapping() -> Tuple[faiss.Index, List[str]]:
    if not os.path.exists(INDEX_PATH) or not os.path.exists(MAPPING_PATH):
        raise FileNotFoundError("FAISS index or mapping file not found. Build it first.")
        
    index = faiss.read_index(INDEX_PATH)
    with open(MAPPING_PATH, 'r') as f:
        id_mapping = json.load(f)
        
    return index, id_mapping

def semantic_search(query_text: str, top_k: int = 50) -> List[Tuple[str, float]]:
    """
    Embeds the query, searches FAISS, returns list of (candidate_id, normalized_score).
    """
    try:
        index, id_mapping = load_index_and_mapping()
    except FileNotFoundError:
        print("Index not found during search. Attempting auto-build...")
        generate_candidate_embeddings()
        index, id_mapping = load_index_and_mapping()
        
    # Embed and reshape query
    query_vec = embed_text(query_text)
    query_vec_2d = np.array([query_vec]).astype('float32')
    
    k = min(top_k, index.ntotal)
    if k == 0:
        return []
        
    # Search the index
    D, I = index.search(query_vec_2d, k)
    
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < len(id_mapping) and idx != -1:
            # Score is Cosine Similarity (max 1.0). Clip nicely to 0-1 for normalized UI representation.
            norm_score = max(0.0, min(1.0, float(score)))
            results.append((id_mapping[idx], norm_score))
            
    return results

def build_index_if_missing():
    """Checks if FAISS vectors exist, and builds them if not."""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(MAPPING_PATH):
        print("FAISS index missing. Initiating build process...")
        generate_candidate_embeddings()
    else:
        print("FAISS index found. Ready for search.")

if __name__ == "__main__":
    # --- Quick Test ---
    print("=== Testing Semantic Search Layer ===")
    jd_query = "Senior Backend Engineer with FastAPI, AWS, Docker"
    print(f"Query: '{jd_query}'\n")
    
    try:
        # We enforce top 10 for the quick test
        top_candidates = semantic_search(jd_query, top_k=10)
        
        if not top_candidates:
            print("No results returned. Ensure MongoDB is populated.")
        else:
            print("Top Candidates:")
            db = connect_db()
            from bson import ObjectId
            
            for i, (cid, score) in enumerate(top_candidates, 1):
                try:
                    candidate = db["candidates"].find_one({"_id": ObjectId(cid)})
                    name = candidate.get("name", "Unknown") if candidate else "Unknown"
                    print(f"{i}. {name} (ID: {cid}) - Score: {score:.4f}")
                except Exception as e:
                    print(f"{i}. ID: {cid} - Score: {score:.4f} - (Error fetching name: {e})")
                    
    except Exception as e:
        print(f"Error during semantic search test: {e}")
