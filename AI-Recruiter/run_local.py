import os
import sys
import time
import argparse

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from backend.ranker import run_ranking
from backend.pre_download import main as download_models

def run_local_pipeline(jd_path, candidates_path, output_path):
    print("="*60)
    print("🚀 REDROB HACKATHON LOCAL RANKING PIPELINE 🚀")
    print("="*60)
    print(f"Job Description : {jd_path}")
    print(f"Candidates      : {candidates_path}")
    print(f"Output CSV      : {output_path}")
    print("="*60)
    
    # 1. Pre-download models (Zero network requirement during ranking)
    print("\n[Step 1] Verifying offline models...")
    download_models()
    
    # 2. Run ranking pipeline
    print("\n[Step 2] Executing 5-minute offline CPU ranker...")
    try:
        run_ranking(jd_path, candidates_path, output_path)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    print("\n" + "="*60)
    print(f"✅ SUCCESS! Final rankings saved to {output_path}")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Redrob candidate ranking pipeline locally.")
    parser.add_argument("--jd", type=str, default="data/job_description.md", help="Path to job_description.md")
    parser.add_argument("--candidates", type=str, default="data/candidates.jsonl", help="Path to candidates.jsonl")
    parser.add_argument("--output", type=str, default="output/submission.csv", help="Path to save the top 100 CSV")
    
    args = parser.parse_args()
    
    # Resolve absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    jd_abs = os.path.join(base_dir, args.jd)
    cand_abs = os.path.join(base_dir, args.candidates)
    out_abs = os.path.join(base_dir, args.output)
    
    if not os.path.exists(jd_abs):
        print(f"❌ Error: JD file not found at {jd_abs}")
        sys.exit(1)
        
    if not os.path.exists(cand_abs):
        print(f"❌ Error: Candidates file not found at {cand_abs}")
        sys.exit(1)
        
    run_local_pipeline(jd_abs, cand_abs, out_abs)
