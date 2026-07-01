import sqlite3
import pandas as pd
import os
import math
from datetime import datetime

# --- BEHAVIORAL SCORING WEIGHTS ---

# RECENCY: moderately important. 
# Active candidates are more likely to respond and engage in the hiring process,
# but an exceptional candidate who is inactive is still worth sourcing.
WEIGHT_RECENCY = 0.3

# ENGAGEMENT: A strong signal of intent and responsiveness to our platform/company.
# Normalizes how frequently they apply and how engaged their profile interactions are.
WEIGHT_ENGAGEMENT = 0.5

# COMPLETENESS: A minor proxy for conscientiousness, detail-orientation, and 
# visibility of their skills to our AI.
WEIGHT_COMPLETENESS = 0.2

def compute_signal_score(row: pd.Series, global_stats: dict) -> float:
    """
    Computes a normalized signal score (0-1) for a single candidate.
    Combines Recency, Engagement, and Profile Completeness using a weighted average.
    """
    # 1. Recency Score (Exponential Decay)
    recency_score = 0.0
    last_active = row.get('last_active_date')
    if pd.notna(last_active) and last_active != "":
        try:
            # Parse date assuming YYYY-MM-DD
            last_active_dt = datetime.strptime(str(last_active), "%Y-%m-%d")
            days_since = (datetime.now() - last_active_dt).days
            if days_since < 0:
                days_since = 0
                
            # Use an exponential decay. Half-life of 365 days means a candidate 
            # active 1 year ago has a recency score of 0.5. 
            # Lambda = ln(2) / half_life = 0.693 / 365 ≈ 0.0019
            recency_score = math.exp(-0.0019 * days_since)
        except Exception:
            pass # Default to 0.0 if parsing fails
            
    # 2. Engagement Score (Min-Max Scaling)
    app_count = float(row.get('application_count', 0))
    app_max = global_stats.get('app_max', 1)
    app_min = global_stats.get('app_min', 0)
    norm_app = (app_count - app_min) / (app_max - app_min) if app_max > app_min else 0.0
    
    eng_score = float(row.get('engagement_score', 0))
    eng_max = global_stats.get('eng_max', 100)
    eng_min = global_stats.get('eng_min', 0)
    norm_eng = (eng_score - eng_min) / (eng_max - eng_min) if eng_max > eng_min else 0.0
    
    engagement_combined = (norm_app + norm_eng) / 2.0
    
    # 3. Profile Completeness
    comp_val = float(row.get('profile_completeness_score', 0))
    # If the score is already 0-1, use it. If > 1, assume it's out of 100 and normalize.
    if comp_val > 1.0:
        comp_val = comp_val / 100.0
    comp_val = max(0.0, min(comp_val, 1.0))
    
    # 4. Final Weighted Average
    final_score = (
        (recency_score * WEIGHT_RECENCY) +
        (engagement_combined * WEIGHT_ENGAGEMENT) +
        (comp_val * WEIGHT_COMPLETENESS)
    )
    
    return final_score

def compute_behavioral_scores(db_path: str):
    """Computes behavioral/activity scores in bulk for all candidates."""
    print("Computing behavioral signals...")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}. Run ingest.py first.")
        
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM candidate_signals", conn)
    
    # Compute global stats required for min-max scaling across the dataset
    global_stats = {
        'app_max': df['application_count'].max() if not df['application_count'].empty else 1,
        'app_min': df['application_count'].min() if not df['application_count'].empty else 0,
        'eng_max': df['engagement_score'].max() if not df['engagement_score'].empty else 100,
        'eng_min': df['engagement_score'].min() if not df['engagement_score'].empty else 0,
    }
    
    scores = []
    for _, row in df.iterrows():
        score = compute_signal_score(row, global_stats)
        scores.append(score)
        
    df['behavioral_score'] = scores
    df.to_sql('candidate_signals', conn, if_exists='replace', index=False)
    conn.close()
    print("Behavioral scoring complete.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_db_path = os.path.join(base_dir, "db", "candidates.db")
    compute_behavioral_scores(test_db_path)
