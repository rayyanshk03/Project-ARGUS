# AI Brain for Modern Hiring - Candidate Ranker PoC

This project is an AI-powered candidate ranking system that takes a job description and a pool of candidate profiles, generating an intelligently ranked shortlist based on semantic relevance and behavioral signals.

## Project Structure
- `/data`: Place raw input files here (e.g., `candidates.csv`, `jd.txt`).
- `/db`: Contains the SQLite database file `candidates.db`.
- `/src`: Source code for the data ingestion, parsing, embedding, scoring, and ranking.
- `/output`: Contains the final `ranked_candidates.csv`.

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python src/main.py`
3. View the results in `output/ranked_candidates.csv`
