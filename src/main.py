import os
import argparse
from ingest import ingest_data
from jd_parser import parse_jd
from embeddings import generate_embeddings
from signal_scoring import compute_behavioral_scores
from ranker import rank_candidates

def main():
    # Setup argparse for command line overrides
    parser = argparse.ArgumentParser(description="AI Brain for Modern Hiring - Pipeline Orchestrator")
    parser.add_argument(
        "--jd", 
        type=str, 
        default="data/jd.txt", 
        help="Path to the Job Description text file (default: data/jd.txt)"
    )
    args = parser.parse_args()

    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(base_dir, "db", "candidates.db")
    CANDIDATES_CSV = os.path.join(base_dir, "data", "candidates.csv")
    OUTPUT_CSV = os.path.join(base_dir, "output", "ranked_candidates.csv")
    
    # Resolve JD Path
    JD_TXT = args.jd if os.path.isabs(args.jd) else os.path.join(base_dir, args.jd)

    print("\n" + "="*50)
    print("=== AI Brain for Modern Hiring: Pipeline Started ===")
    print("="*50)
    
    if not os.path.exists(JD_TXT):
        print(f"\n[ERROR] Job description file not found at: {JD_TXT}")
        print("Please provide a valid file using --jd or create data/jd.txt")
        return

    # Step 1: Ingest Data
    print("\n[1/5] --- Ingesting Candidate Data ---")
    ingest_data(CANDIDATES_CSV, DB_PATH)
    
    # Step 2: Parse Job Description
    print("\n[2/5] --- Parsing Job Description ---")
    with open(JD_TXT, 'r', encoding='utf-8') as f:
        raw_jd = f.read()
    parsed_jd = parse_jd(raw_jd)
    print(f"Parsed Requirements: {parsed_jd}")
    
    # Step 3: Generate Embeddings & Semantic Scores
    print("\n[3/5] --- Generating Embeddings & Semantic Scores ---")
    semantic_results = generate_embeddings(DB_PATH, parsed_jd)
    
    # Step 4: Compute Behavioral Signals
    print("\n[4/5] --- Computing Behavioral Signals ---")
    compute_behavioral_scores(DB_PATH)
    
    # Step 5: Rank Candidates (Applies Eligibility Filter internally)
    print("\n[5/5] --- Applying Eligibility Filters & Final Ranking ---")
    rank_candidates(DB_PATH, semantic_results, parsed_jd, OUTPUT_CSV)
    
    print("\n" + "="*50)
    print("=== Pipeline Completed Successfully ===")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
