import sqlite3
import pandas as pd
import os
import re

# --- FINAL RANKING WEIGHTS ---
WEIGHT_SEMANTIC = 0.5
WEIGHT_SIGNAL = 0.3
WEIGHT_ELIGIBILITY = 0.2

def check_eligibility(candidate_row: pd.Series, jd_requirements: dict) -> tuple:
    """
    Evaluates candidate eligibility based on experience and skills.
    Returns: (eligibility_score, matching_skills_str, missing_skills_str)
    """
    min_exp = float(jd_requirements.get('min_experience_years', 0))
    cand_exp = float(candidate_row.get('experience_years', 0))
    
    cand_skills_raw = str(candidate_row.get('skills', '')).lower()
    req_skills = [str(s).lower() for s in jd_requirements.get('required_skills', [])]
    
    matching = []
    missing = []
    
    for skill in req_skills:
        # Exact word boundary match for skills
        if re.search(r'\b' + re.escape(skill) + r'\b', cand_skills_raw):
            matching.append(skill)
        else:
            missing.append(skill)
            
    if not req_skills:
        skill_coverage = 1.0
    else:
        skill_coverage = len(matching) / len(req_skills)
        
    # Determine eligibility score (0.2, 0.5, or 1.0)
    if cand_exp < min_exp:
        eligibility_score = 0.2
    elif skill_coverage >= 0.70:
        eligibility_score = 1.0
    else:
        eligibility_score = 0.5
        
    return (eligibility_score, "; ".join(matching), "; ".join(missing))

def rank_candidates(db_path: str, semantic_results: list, jd_requirements: dict, output_csv: str):
    """Combines all scoring layers into a final ranking and generates a detailed CSV."""
    print("Ranking candidates...")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}. Run ingest.py first.")
        
    conn = sqlite3.connect(db_path)
    
    # semantic_results is a list of (candidate_id, semantic_score)
    semantic_df = pd.DataFrame(semantic_results, columns=['id', 'semantic_score'])
    
    # Fetch candidates and signals
    query = """
    SELECT c.id, c.name, c.experience_years, c.skills, s.behavioral_score as signal_score
    FROM candidates c
    JOIN candidate_signals s ON c.id = s.candidate_id
    """
    db_df = pd.read_sql_query(query, conn)
    
    # Merge semantic scores with database data
    df = pd.merge(semantic_df, db_df, on='id')
    
    eligibility_scores = []
    matching_skills_list = []
    missing_skills_list = []
    
    for _, row in df.iterrows():
        e_score, matching, missing = check_eligibility(row, jd_requirements)
        eligibility_scores.append(e_score)
        matching_skills_list.append(matching)
        missing_skills_list.append(missing)
        
    df['eligibility_score'] = eligibility_scores
    df['key_matching_skills'] = matching_skills_list
    df['missing_skills'] = missing_skills_list
    
    # Calculate final score (Additive equation per requirements)
    df['final_score'] = (
        (df['semantic_score'] * WEIGHT_SEMANTIC) + 
        (df['signal_score'] * WEIGHT_SIGNAL) + 
        (df['eligibility_score'] * WEIGHT_ELIGIBILITY)
    )
    
    # Sort descending
    df_ranked = df.sort_values(by='final_score', ascending=False).reset_index(drop=True)
    
    # Assign rank (1-indexed)
    df_ranked['rank'] = df_ranked.index + 1
    
    # Rename columns to match requested output exactly
    df_ranked = df_ranked.rename(columns={'id': 'candidate_id', 'name': 'candidate_name'})
    
    # Select final columns in order
    final_columns = [
        'rank', 'candidate_id', 'candidate_name', 'final_score', 'semantic_score', 
        'signal_score', 'eligibility_score', 'key_matching_skills', 'missing_skills'
    ]
    df_output = df_ranked[final_columns]
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_output.to_csv(output_csv, index=False)
    print(f"Ranking complete! Saved {len(df_output)} candidates to {output_csv}")
    
    print("\n--- TOP 3 CANDIDATES ---")
    top_3 = df_output.head(3)
    for i, row in top_3.iterrows():
        print(f"#{row['rank']} {row['candidate_name']} (Score: {row['final_score']:.3f}) - Semantic: {row['semantic_score']:.3f}, Signal: {row['signal_score']:.3f}, Elig: {row['eligibility_score']:.1f}")
        
    conn.close()

if __name__ == "__main__":
    pass
