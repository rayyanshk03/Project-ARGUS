import pandas as pd
import sqlite3
import os

def ingest_data(csv_path: str, db_path: str):
    """Loads candidate data from CSV into a SQLite database with a 2-table schema."""
    print(f"Ingesting candidates from {csv_path}...")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input file not found: {csv_path}")
        
    df = pd.read_csv(csv_path)
    
    # Check for nulls in the original df to report
    null_counts = df.isna().sum()
    
    # --- Clean/normalize text fields ---
    text_columns = ['name', 'skills', 'education', 'past_roles', 'location', 'last_active_date']
    for col in text_columns:
        if col in df.columns:
            # Handle nulls, strip whitespace, and lower-case
            df[col] = df[col].fillna("").astype(str).str.strip().str.lower()
            
    # Handle numeric fields
    df['experience_years'] = df['experience_years'].fillna(0).astype(int)
    df['application_count'] = df['application_count'].fillna(0).astype(int)
    df['engagement_score'] = df['engagement_score'].fillna(0.0).astype(float)
    df['profile_completeness_score'] = df['profile_completeness_score'].fillna(0.0).astype(float)
            
    # --- Build raw_profile_text ---
    df['raw_profile_text'] = (
        "skills: " + df['skills'] + " | " +
        "experience years: " + df['experience_years'].astype(str) + " | " +
        "past roles: " + df['past_roles'] + " | " +
        "education: " + df['education']
    )
    
    # --- Split into two tables ---
    candidates_df = df[['id', 'name', 'skills', 'experience_years', 'education', 'past_roles', 'location', 'raw_profile_text']]
    candidate_signals_df = df[['id', 'last_active_date', 'application_count', 'engagement_score', 'profile_completeness_score']].copy()
    # Rename id to candidate_id in signals table for clarity as foreign key
    candidate_signals_df = candidate_signals_df.rename(columns={'id': 'candidate_id'})
    
    # Ensure db directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    
    # Save to database
    candidates_df.to_sql('candidates', conn, if_exists='replace', index=False)
    candidate_signals_df.to_sql('candidate_signals', conn, if_exists='replace', index=False)
    
    # Verify by reading back
    total_candidates = pd.read_sql_query("SELECT COUNT(*) as cnt FROM candidates", conn).iloc[0]['cnt']
    total_signals = pd.read_sql_query("SELECT COUNT(*) as cnt FROM candidate_signals", conn).iloc[0]['cnt']
    
    print("\n--- INGESTION SUMMARY ---")
    print(f"Rows in 'candidates' table: {total_candidates}")
    print(f"Rows in 'candidate_signals' table: {total_signals}")
    
    print("\nNull/Empty values handled in source data:")
    print(null_counts[null_counts > 0].to_string() if not null_counts[null_counts > 0].empty else "No missing values found.")
    
    print("\nSample row from 'candidates':")
    sample_candidate = pd.read_sql_query("SELECT * FROM candidates LIMIT 1", conn)
    print(sample_candidate.iloc[0].to_dict())
    
    print("\nSample row from 'candidate_signals':")
    sample_signal = pd.read_sql_query("SELECT * FROM candidate_signals LIMIT 1", conn)
    print(sample_signal.iloc[0].to_dict())
    print("-------------------------\n")
    
    conn.close()

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_csv_path = os.path.join(base_dir, "data", "candidates.csv")
    test_db_path = os.path.join(base_dir, "db", "candidates.db")
    ingest_data(test_csv_path, test_db_path)
