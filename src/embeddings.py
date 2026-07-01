import sqlite3
import pandas as pd
import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

def generate_embeddings(db_path: str, parsed_jd: dict) -> list:
    """Generates embeddings, stores them, computes cosine similarity, and returns semantic scores."""
    print("Initializing embedding model (this may take a moment to download on first run)...")
    # Using a fast, lightweight local embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 1. Embed Job Description
    print("Generating embedding for Job Description...")
    jd_text = (
        f"skills: {'; '.join(parsed_jd.get('required_skills', []))} | "
        f"experience years: {parsed_jd.get('min_experience_years', 0)} | "
        f"role: {parsed_jd.get('role_level', '')} | "
        f"domain: {parsed_jd.get('domain', '')}"
    )
    jd_embedding = model.encode(jd_text)
    
    # 2. Embed Candidates
    print("Generating embeddings for candidates...")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}. Please run ingest.py first.")
        
    conn = sqlite3.connect(db_path)
    
    # Ensure the table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'")
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Table 'candidates' does not exist. Please run ingest.py first.")
        
    df = pd.read_sql_query("SELECT * FROM candidates", conn)
    
    # Use the pre-computed raw_profile_text
    candidate_texts = df['raw_profile_text'].tolist()
    candidate_embeddings = model.encode(candidate_texts)
    
    # Store embeddings in the database
    df['embedding'] = [json.dumps(emb.tolist()) for emb in candidate_embeddings]
    df.to_sql('candidates', conn, if_exists='replace', index=False)
    
    # 3. Compute cosine similarity between JD and every candidate
    jd_emb_array = np.array(jd_embedding).reshape(1, -1)
    sim_scores = cosine_similarity(jd_emb_array, candidate_embeddings)[0]
    
    # Normalize to 0-1
    normalized_scores = (sim_scores + 1) / 2
    
    # Return a sorted list of (candidate_id, semantic_score)
    results = []
    for idx, row in df.iterrows():
        results.append((int(row['id']), float(normalized_scores[idx])))
        
    results.sort(key=lambda x: x[1], reverse=True)
    
    conn.close()
    
    return results

if __name__ == "__main__":
    # Test block
    mock_parsed_jd = {
        "required_skills": ["python", "machine learning"],
        "nice_to_have_skills": [],
        "min_experience_years": 3,
        "role_level": "mid",
        "domain": "AI"
    }
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_db_path = os.path.join(base_dir, "db", "candidates.db")
    
    semantic_results = generate_embeddings(test_db_path, mock_parsed_jd)
    print("Semantic Scores (Candidate ID, Score):")
    for r in semantic_results:
        print(f"ID: {r[0]}, Score: {r[1]:.4f}")
