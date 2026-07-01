import os
import sys
from typing import List, Dict, Any
import json

# Import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from embeddings import semantic_search
from llm import MODEL_NAME, anthropic_client
from parser import connect_db
from bson import ObjectId

def retrieve_relevant_chunks(query: str, top_k: int = 10) -> List[Dict[str, str]]:
    """
    Uses the existing FAISS index to semantically retrieve top relevant 
    candidate raw_resume_text (or generated text) for the query.
    """
    pool = semantic_search(query, top_k=top_k)
    db = connect_db()
    
    excerpts = []
    for cid, score in pool:
        doc = db["candidates"].find_one({"_id": ObjectId(cid)})
        if not doc:
            continue
            
        # We rely on raw_resume_text if available, otherwise reconstruct a comprehensive text blob
        raw_text = doc.get("raw_resume_text")
        if not raw_text:
            raw_text = f"Skills: {', '.join(doc.get('skills', []))}. "
            for p in doc.get("projects", []):
                raw_text += f"Project {p.get('title', '')}: {p.get('description', '')}. "
            for role in doc.get("past_roles", []):
                raw_text += f"Role {role.get('title', '')} at {role.get('company', '')}: {role.get('description', '')}. "
                
        excerpts.append({
            "candidate_id": cid,
            "name": doc.get("name", "Unknown"),
            "text": raw_text
        })
        
    return excerpts


def answer_with_evidence(query: str) -> Dict[str, Any]:
    """
    Retrieves chunks and calls Claude with strict grounding prompts to answer 
    the recruiter query based ONLY on the provided context. Returns the natural
    language answer and cited candidate IDs.
    """
    excerpts = retrieve_relevant_chunks(query, top_k=10)
    
    if not excerpts:
        return {
            "answer": "No relevant candidates found in the database for this query.",
            "cited_candidate_ids": []
        }
        
    context_str = ""
    candidate_ids = []
    
    for exc in excerpts:
        cid = exc["candidate_id"]
        candidate_ids.append(cid)
        # Using [ID] brackets to make it explicit for Claude to cite
        context_str += f"\n--- CANDIDATE [{cid}] ({exc['name']}) ---\n{exc['text']}\n"
        
    system_prompt = """You are an expert technical recruiter assistant.
Your job is to answer the user's question based STRICTLY AND EXCLUSIVELY on the provided candidate excerpts below.

CRITICAL RULES TO PREVENT HALLUCINATION:
1. Answer ONLY using the provided candidate excerpts. Do not hallucinate or use outside knowledge.
2. If no candidates match the query criteria in the provided text, say so clearly.
3. For EVERY candidate you mention, you MUST explicitly cite them using their exact exact [candidate_id] bracket format provided in the text.
4. Keep the answer professional and highlight the specific evidence found in the text.
"""

    prompt = f"""
USER QUERY: {query}

EVIDENCE CONTEXT:
{context_str}
"""

    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your_anthropic_api_key_here":
        return {
            "answer": "RAG endpoint requires an active Anthropic API key to generate evidence-based answers.",
            "cited_candidate_ids": []
        }
        
    try:
        response = anthropic_client.messages.create(
            model=MODEL_NAME,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0 # Strictly 0.0 to prevent hallucination in RAG pipelines
        )
        answer = response.content[0].text.strip()
        
        # Dynamically extract cited IDs by checking which candidate IDs appear in the LLM's response
        cited_ids = []
        for cid in candidate_ids:
            if cid in answer:
                cited_ids.append(cid)
                
        return {
            "answer": answer,
            "cited_candidate_ids": cited_ids
        }
    except Exception as e:
        print(f"RAG LLM failed: {e}")
        return {
            "answer": f"Error generating answer: {e}",
            "cited_candidate_ids": []
        }
