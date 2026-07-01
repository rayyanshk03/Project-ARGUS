import os
import sys
from pprint import pprint

# Ensure the backend module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.parser import connect_db

def main():
    db = connect_db()
    
    print("========== SAMPLE CANDIDATES ==========")
    candidates = list(db["candidates"].find().limit(5))
    if not candidates:
        print("No candidates found in the database. Run ingest_csv_to_mongo first.")
    else:
        for idx, c in enumerate(candidates, 1):
            print(f"\n--- Candidate {idx} ---")
            # Truncate raw_resume_text for readable output
            if 'raw_resume_text' in c and isinstance(c['raw_resume_text'], str):
                c['raw_resume_text'] = c['raw_resume_text'][:100] + "... [TRUNCATED]"
            pprint(c)
            
    print("\n\n========== SAMPLE BEHAVIOR RECORDS ==========")
    behavior = list(db["candidate_behavior"].find().limit(5))
    if not behavior:
        print("No candidate behavior records found in the database. Run ingest_csv_to_mongo first.")
    else:
        for idx, b in enumerate(behavior, 1):
            print(f"\n--- Behavior Record {idx} ---")
            pprint(b)

if __name__ == "__main__":
    main()
