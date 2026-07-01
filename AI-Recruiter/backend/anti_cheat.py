from typing import List, Dict, Any, Set
from collections import Counter
import re

def is_keyword_stuffer(candidate: Dict[str, Any]) -> bool:
    """
    Detects keyword stuffing by looking for:
    1. Unnaturally high number of raw skills listed (> 50 distinct skills is suspicious, >100 is almost certainly a trap).
    2. Repeated words in resume text (same word repeated > 20 times in a row).
    """
    skills = candidate.get("skills", [])
    if isinstance(skills, list) and len(skills) > 80:
        return True
        
    text = candidate.get("raw_resume_text", "").lower()
    if not text:
        return False
        
    words = re.findall(r'\b\w+\b', text)
    if not words:
        return False
        
    # Check for excessive repetition of exact same words
    word_counts = Counter(words)
    # If the most common word (excluding common stop words if we had them) appears too many times
    # A simple trap is just repeating "python python python..."
    if word_counts:
        top_word, count = word_counts.most_common(1)[0]
        # If a single word makes up more than 15% of a decently sized resume, it's stuffing
        if len(words) > 50 and count / len(words) > 0.15 and len(top_word) > 2:
            return True
            
    return False

def is_impossible_experience(candidate: Dict[str, Any]) -> bool:
    """
    Detects impossible experience:
    - > 50 years of experience (highly unlikely in a generic dataset, often a honeypot).
    - Overlapping jobs that sum to impossible totals (we'll just use the raw experience_years field for now).
    """
    exp = candidate.get("experience_years", 0)
    try:
        exp = float(exp)
        if exp > 45.0:
            return True
    except (ValueError, TypeError):
        pass
        
    return False

def is_plain_language_tier5(candidate: Dict[str, Any]) -> bool:
    """
    Detects candidates that are essentially empty or say things like 'I am a good worker'.
    """
    text = candidate.get("raw_resume_text", "").strip()
    # It's plain language if there are no skills, and text is short
    skills = candidate.get("skills", [])
    if len(text) < 50 and not skills:
        return True
    return False

def filter_candidates(pool_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Applies all filters to a batch of candidates.
    Also handles behavioral twin filtering (exact duplicate resumes with different IDs).
    """
    valid = []
    seen_hashes: Set[int] = set()
    
    for cand in pool_candidates:
        if is_keyword_stuffer(cand):
            continue
        if is_impossible_experience(cand):
            continue
        if is_plain_language_tier5(cand):
            continue
            
        # Behavioral twin detection (hash the raw text or skills)
        text = cand.get("raw_resume_text", "")
        # If no text, hash the skills
        if not text:
            text = ",".join(sorted([str(s) for s in cand.get("skills", [])]))
            
        text_hash = hash(text)
        if text_hash in seen_hashes:
            continue
            
        seen_hashes.add(text_hash)
        valid.append(cand)
        
    return valid
