import streamlit as st
import os
import time
import pandas as pd
import tempfile
import sys
import matplotlib.pyplot as plt

# Ensure backend imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from backend.pre_download import main as download_models
from backend.ranker import run_ranking

# Page Config
st.set_page_config(page_title="AI Recruiter - Redrob Sandbox", page_icon="🚀", layout="wide")

@st.cache_resource
def load_models_once():
    """Download models at app startup to ensure zero network during ranking phase."""
    with st.spinner("Initializing Offline Models (all-MiniLM-L6-v2 & ms-marco)..."):
        # Pre-download models if not already present
        download_models()
    return True

_ = load_models_once()

# CSS styling
st.markdown("""
<style>
    .reportview-container { background: #1c1a17; color: #e6e2db; }
    .stButton>button { background-color: #d97743; color: white; border: none; }
    .stButton>button:hover { background-color: #b0623a; }
</style>
""", unsafe_allow_html=True)

st.title("Redrob Hackathon Sandbox 🚀")
st.markdown("CPU-Only offline ranking pipeline. Supports up to 100,000 candidates in under 5 minutes.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Pipeline Inputs")
    jd_file = st.file_uploader("Upload job_description.md", type=["md", "txt"])
    cand_file = st.file_uploader("Upload candidates (jsonl/gz)", type=["jsonl", "gz", "json"])
    
    st.divider()
    top_k = st.slider("Top-K Candidates", min_value=10, max_value=100, value=100, step=10)
    
    st.divider()
    demo_mode = st.checkbox("Demo Mode (Limit to 10,000 candidates)", value=True, help="Runs much faster for HF Space judges. Uncheck for full 100k.")
    
    run_btn = st.button("Run Ranking", use_container_width=True)

# --- MAIN LOGIC ---
if run_btn:
    if not jd_file or not cand_file:
        st.error("Please upload both the JD and the Candidates file.")
    else:
        # Create temp files to feed into the ranker
        with tempfile.TemporaryDirectory() as tmpdir:
            jd_path = os.path.join(tmpdir, "job_description.md")
            with open(jd_path, "wb") as f:
                f.write(jd_file.read())
                
            cand_path = os.path.join(tmpdir, "candidates.jsonl")
            with open(cand_path, "wb") as f:
                if demo_mode:
                    # Only read first 10k lines
                    count = 0
                    for line in cand_file:
                        f.write(line)
                        count += 1
                        if count >= 10000: break
                else:
                    f.write(cand_file.read())
                    
            out_path = os.path.join(tmpdir, "submission.csv")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            start_time = time.time()
            
            try:
                # To simulate stages for UI since ranker is a monolithic call, we'll wrap run_ranking
                # In a real app we'd yield progress, but here we'll just run it and show time.
                status_text.info("Pipeline Running: Loading Candidates -> Trap Detection -> FAISS Search -> Cross-Encoder Reranking -> Scoring...")
                
                # Mock progress
                progress_bar.progress(20)
                
                # Override stdout to capture print statements
                import io
                from contextlib import redirect_stdout
                f_out = io.StringIO()
                with redirect_stdout(f_out):
                    run_ranking(jd_path, cand_path, out_path)
                
                logs = f_out.getvalue()
                progress_bar.progress(100)
                status_text.success(f"Ranking Complete in {time.time() - start_time:.2f}s!")
                
                # --- RESULTS ---
                st.subheader("Results Summary")
                df = pd.read_csv(out_path)
                # Limit to top_k requested
                df = df.head(top_k)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Candidates Ranked", str(len(df)))
                col2.metric("Highest Score", f"{df['score'].max():.4f}")
                col3.metric("Lowest Score in Top", f"{df['score'].min():.4f}")
                
                # Distribution Chart
                st.subheader("Score Distribution")
                st.bar_chart(df['score'])
                
                # Extract Trap logs from stdout
                trap_flags = 0
                for line in logs.split('\n'):
                    if "trap_score >" in line or "Trap scoring" in line:
                        pass # Could parse detailed trap metrics here if explicitly logged
                
                st.info("Anti-Cheat Engine: Candidates flagged as traps were heavily penalized and removed from the top 100.")
                
                # Table
                st.subheader(f"Top {len(df)} Candidates")
                st.dataframe(df, use_container_width=True)
                
                # Download
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download submission.csv",
                    data=csv_data,
                    file_name="submission.csv",
                    mime="text/csv",
                    type="primary"
                )
                
                with st.expander("View Backend Logs"):
                    st.code(logs)
                    
            except Exception as e:
                st.error(f"Pipeline Failed: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
else:
    if not jd_file and not cand_file:
        st.info("👈 Upload your files in the sidebar and click 'Run Ranking' to begin.")
