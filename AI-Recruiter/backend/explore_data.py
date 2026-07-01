import json
import gzip
import os
import psutil
import pandas as pd
from collections import defaultdict

# --- CONFIG ---
SAMPLE_PATH = "/Users/rayyanshaikh/Desktop/India_runs_data_and_ai_challenge/sample_candidates.json"
FULL_PATH = "/Users/rayyanshaikh/Desktop/India_runs_data_and_ai_challenge/candidates.jsonl"

def print_memory(label):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)
    print(f"[MEMORY] {label}: {mem:.2f} MB")

def step1_load_and_inspect():
    print("\n--- STEP 1: Load and Inspect sample_candidates.json ---")
    if not os.path.exists(SAMPLE_PATH):
        print(f"Warning: {SAMPLE_PATH} not found.")
        return []
        
    with open(SAMPLE_PATH, 'r') as f:
        samples = json.load(f)
        
    print(f"Loaded {len(samples)} candidates.")
    
    if not samples: return []
    
    # 1. Print full schema
    print("\n[Schema of first candidate]")
    first = samples[0]
    for k, v in first.items():
        print(f"  {k}: {type(v).__name__} (Example: {str(v)[:50]})")
        
    # 2. Print null/missing counts
    print("\n[Null/Missing counts]")
    counts = defaultdict(int)
    for c in samples:
        for k in first.keys():
            val = c.get(k)
            if val is None or val == "" or val == []:
                counts[k] += 1
    for k, count in counts.items():
        print(f"  {k}: {count}/{len(samples)} missing")
        
    # 3. Categorical distribution (naive detection) & Numeric stats
    print("\n[Categorical Distributions & Numeric Stats]")
    stats = defaultdict(list)
    for c in samples:
        for k, v in c.items():
            if isinstance(v, (int, float)):
                stats[k].append(v)
            elif isinstance(v, str) and len(v) < 50:
                stats[k].append(v)
                
    for k, vals in stats.items():
        if isinstance(vals[0], (int, float)):
            print(f"  {k} (Numeric): Min={min(vals)}, Max={max(vals)}, Mean={sum(vals)/len(vals):.2f}")
        else:
            unique = set(vals)
            if len(unique) <= 10:
                dist = {u: vals.count(u) for u in unique}
                print(f"  {k} (Categorical): {dist}")
                
    return samples

def step2_understand_redrob_signals(samples):
    print("\n--- STEP 2: Understand redrob_signals ---")
    if not samples: return
    
    all_signals = defaultdict(list)
    for c in samples:
        sigs = c.get("redrob_signals", {})
        for k, v in sigs.items():
            all_signals[k].append(v)
            
    print(f"Found {len(all_signals)} distinct signals.")
    for k, vals in all_signals.items():
        populated = len(vals) / len(samples) * 100
        typ = type(vals[0]).__name__
        val_range = ""
        if typ in ["int", "float"]:
            val_range = f"[{min(vals)} to {max(vals)}]"
        print(f"  {k}: Type={typ}, Populated={populated:.1f}%, Range={val_range}")
        
    print("\n[Likely Categories]")
    print("  - Recency Signals: last_active_date, signup_date")
    print("  - Engagement Signals: recruiter_response_rate, avg_response_time_hours")
    print("  - Quality Signals: github_activity_score, endorsements_received, skill_assessment_scores")
    print("  - Completeness Signals: profile_completeness_score, verified_email, linkedin_connected")

def flag_suspicious(candidate):
    score = 0.0
    reasons = []
    
    # 1. Experience Check
    exp = 0
    try:
        exp = float(candidate.get("experience_years", 0) or 0)
    except:
        pass
        
    skills = candidate.get("skills", [])
    if isinstance(skills, list) and len(skills) > 80:
        score += 0.5
        reasons.append(f"Keyword stuffing: {len(skills)} skills listed.")
        
    if exp > 45:
        score += 0.5
        reasons.append(f"Impossible experience: {exp} years.")
        
    # 2. Behavioral Signals Check
    sigs = candidate.get("redrob_signals", {})
    maxed_out = 0
    for v in sigs.values():
        if isinstance(v, (int, float)) and v >= 999:
            maxed_out += 1
            
    if maxed_out >= 3:
        score += 0.4
        reasons.append(f"Suspicious signals: {maxed_out} signals are maxed out (999/100%).")
        
    return min(1.0, score), reasons

def step3_honeypot_research(samples):
    print("\n--- STEP 3: Honeypot Detection Research ---")
    print("Flagging logic written. Testing on samples:")
    for c in samples[:5]:
        score, reasons = flag_suspicious(c)
        if score > 0:
            print(f"  {c.get('name', 'Unknown')} -> Score: {score}, Reasons: {reasons}")
        else:
            print(f"  {c.get('name', 'Unknown')} -> Clear")

def step4_load_full_dataset():
    print("\n--- STEP 4: Load 100k Dataset Efficiently ---")
    if not os.path.exists(FULL_PATH):
        print(f"Warning: {FULL_PATH} not found. Ensure it is in the same directory.")
        return None
        
    print_memory("Before loading")
    
    # Efficient streaming: Only keep required columns
    required_cols = ["candidate_id", "name", "experience_years", "skills", "redrob_signals", "raw_resume_text"]
    records = []
    
    try:
        # It's uncompressed jsonl
        with open(FULL_PATH, 'r') as f:
            for i, line in enumerate(f):
                if not line.strip(): continue
                data = json.loads(line)
                # Filter strictly required fields
                filtered = {k: data.get(k) for k in required_cols}
                records.append(filtered)
                if i > 0 and i % 20000 == 0:
                    print(f"  Loaded {i} records...")
                    
        df = pd.DataFrame(records)
        print(f"Successfully loaded {len(df)} records into DataFrame.")
        print_memory("After loading into DataFrame")
        return df
    except Exception as e:
        print(f"Error loading jsonl: {e}")
        return None

def step5_interesting_candidates(df, samples):
    print("\n--- STEP 5: Interesting Candidates ---")
    if df is None or len(df) == 0:
        return
        
    # Let's find one of each using our heuristics
    strong_match = None
    keyword_stuffer = None
    honeypot = None
    
    # Convert DF back to dicts for easy filtering
    pool = df.to_dict('records')
    
    for c in pool:
        score, reasons = flag_suspicious(c)
        if score >= 1.0 and "Impossible experience" in str(reasons) and not honeypot:
            honeypot = c
        elif score >= 0.5 and "Keyword stuffing" in str(reasons) and not keyword_stuffer:
            keyword_stuffer = c
        elif score == 0 and not strong_match:
            strong_match = c
            
        if strong_match and keyword_stuffer and honeypot:
            break
            
    print(f"1. Typical Match: {strong_match['name']} ({strong_match.get('experience_years')} yrs, {len(strong_match.get('skills', []))} skills)")
    if keyword_stuffer:
        print(f"2. Keyword Stuffer: {keyword_stuffer['name']} ({len(keyword_stuffer.get('skills', []))} skills)")
    if honeypot:
        print(f"3. Honeypot: {honeypot['name']} ({honeypot.get('experience_years')} yrs)")

if __name__ == "__main__":
    print_memory("Initial")
    samples = step1_load_and_inspect()
    step2_understand_redrob_signals(samples)
    step3_honeypot_research(samples)
    df = step4_load_full_dataset()
    step5_interesting_candidates(df, samples)
