"""Conservative heuristic extraction (no LLM, phrase matching only)."""

import re


# Simple phrase patterns for heuristic matching
HEURISTIC_PATTERNS = [
    # Values
    (r'\b(?:I value|I care about|important to me|matters to me)\b', 'values'),
    # Boundaries
    (r'\b(?:I don\'t|I won\'t|I refuse to|boundary|limit)\b', 'boundaries'),
    # Needs
    (r'\b(?:I need|need to|must have|require)\b', 'needs'),
    # Fears
    (r'\b(?:I fear|I\'m afraid|worries me|scares me|anxious about)\b', 'fears'),
    # Goals
    (r'\b(?:I want to|I\'m working toward|goal|aim to|plan to)\b', 'goals_now'),
    # Strengths
    (r'\b(?:I\'m good at|strength|excel at|talented at)\b', 'strengths'),
    # Weaknesses
    (r'\b(?:I struggle with|weakness|bad at|difficult for me)\b', 'weaknesses'),
]


def extract_heuristics(text: str) -> list[tuple[str, str]]:
    """
    Extract conservative heuristic suggestions from text.

    Returns list of (field, suggestion_text) tuples.
    Only runs if no tagged lines were found.
    """
    if not text or not text.strip():
        return []

    proposals = []

    for pattern, field in HEURISTIC_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            # Found a match, suggest the entire text for this field
            # Keep it simple: propose the full text
            proposals.append((field, text.strip()))
            # Only return first match to keep conservative
            break

    return proposals
