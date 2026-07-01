# AI-Recruiter

AI-Recruiter is an AI recruitment ranking system.

## Folder Structure

- `backend/`: Contains the FastAPI application and core logic for parsing, embedding, ranking, and API endpoints.
- `frontend/`: Contains the frontend user interface.
- `requirements.txt`: Python dependencies.
- `.env.example`: Example environment variables configuration.

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```

3. Run the backend server:
   ```bash
   cd backend
   uvicorn app:app --reload
   ```
