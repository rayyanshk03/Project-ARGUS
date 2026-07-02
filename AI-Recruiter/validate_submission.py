import pandas as pd
import sys
import os

def run_validation(csv_path: str):
    print(f"Validating {csv_path}...")
    if not os.path.exists(csv_path):
        print(f"[NO-GO] File {csv_path} not found!")
        sys.exit(1)
        
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[NO-GO] Could not parse CSV: {e}")
        sys.exit(1)
        
    # Check 1: Exactly 100 rows
    if len(df) != 100:
        print(f"[NO-GO] Expected exactly 100 rows, got {len(df)}")
        sys.exit(1)
        
    # Check 2: Columns match
    expected_cols = ["rank", "candidate_id", "score", "reasoning"]
    for c in expected_cols:
        if c not in df.columns:
            print(f"[NO-GO] Missing expected column: {c}")
            sys.exit(1)
            
    # Check 3: No duplicate candidate_ids
    if len(df["candidate_id"].unique()) != 100:
        print("[NO-GO] Duplicate candidate_ids found!")
        sys.exit(1)
        
    # Check 4: Scores strictly descending (or equal)
    scores = df["score"].tolist()
    for i in range(len(scores)-1):
        if scores[i] < scores[i+1]:
            print(f"[NO-GO] Scores are not descending: row {i} ({scores[i]}) < row {i+1} ({scores[i+1]})")
            sys.exit(1)
            
    # Check 5: Reasoning non-empty
    if df["reasoning"].isnull().any():
        print("[NO-GO] Empty reasoning found in one or more rows!")
        sys.exit(1)
        
    for idx, r in enumerate(df["reasoning"]):
        if str(r).strip() == "":
            print(f"[NO-GO] Empty reasoning string found at row {idx}!")
            sys.exit(1)
            
    print("[GO] Validation Passed! All constraints met. Safe for submission.")
    sys.exit(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate submission CSV")
    parser.add_argument("--file", type=str, default="backend/output/rankings.csv", help="Path to submission CSV")
    args = parser.parse_args()
    
    run_validation(args.file)
