---
title: Redrob AI Recruiter Sandbox
emoji: 🚀
colorFrom: blue
colorTo: orange
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: false
---

# Redrob Hackathon: AI Candidate Ranking Sandbox

This HuggingFace Space serves as the interactive sandbox and demo for our Redrob Hackathon submission. 

## What This App Does
This application ranks a pool of 100,000 candidates against a specific job description (`job_description.md`) using a robust, highly optimized, multi-stage AI pipeline. The entire end-to-end pipeline executes on CPU-only hardware (16GB RAM) in under 5 minutes without any network calls at runtime.

It utilizes:
1. **Semantic Search via FAISS**: Fast first-pass retrieval using `all-MiniLM-L6-v2`.
2. **Cross-Encoder Reranking**: Advanced contextual analysis of the top 500 candidates using `ms-marco-MiniLM-L-6-v2`.
3. **Multi-Factor Scoring Engine**: Precisely weights semantic matches, skill overlaps, years of experience, and behavioral signals (recency, engagement, etc.).
4. **Anti-Cheat Trap Detectors**: Identifies "Honeypots", "Keyword Stuffers", and "Behavioral Twins", ruthlessly penalizing their scores to keep the top 100 pure.

## How to Use the Sandbox
1. **Upload Data**: Use the sidebar to upload the candidate dataset (`candidates.jsonl` or `.jsonl.gz`) and the `job_description.md` file.
2. **Demo Mode vs Full Mode**: 
   - **Demo Mode (Checked by default)**: Runs the entire pipeline on the first 10,000 candidates. This allows judges to rapidly test the logic and UI on HuggingFace's free 2vCPU tier without waiting 5 minutes.
   - **Full Mode**: Uncheck Demo Mode to run against the full 100k candidate pool (Requires patience on free CPU instances, runs in ~4.5 minutes locally).
3. **Run Ranking**: Click the primary action button to execute the pipeline. You will see progress indicators for each stage.
4. **Review Results**: View the summary statistics, score distribution, and trap detection rate. 
5. **Download**: Click "Download final submission CSV" to export the generated top-100 rankings in the format required for scoring.

## Model and Approach
- All models are pre-downloaded to comply with zero-network restrictions.
- Skill synonyms are dynamically expanded using a custom extraction dictionary to ensure maximum recall.
- Template-driven reasoning generation creates personalized, natural language summaries for each candidate instantly.
