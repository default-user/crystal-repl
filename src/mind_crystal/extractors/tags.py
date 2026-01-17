"""Tag extraction from user messages."""

import re
from typing import Optional


# Tag vocabulary mapping
TAG_MAP = {
    'value': 'values',
    'values': 'values',
    'nonnegotiable': 'non_negotiables',
    'non_negotiables': 'non_negotiables',
    'non-negotiables': 'non_negotiables',
    'boundary': 'boundaries',
    'boundaries': 'boundaries',
    'need': 'needs',
    'needs': 'needs',
    'fear': 'fears',
    'fears': 'fears',
    'goal': 'goals_now',
    'goals': 'goals_now',
    'goal_now': 'goals_now',
    'goals_now': 'goals_now',
    'goal-now': 'goals_now',
    'goals-now': 'goals_now',
    'goal_long': 'goals_long',
    'goals_long': 'goals_long',
    'goal-long': 'goals_long',
    'goals-long': 'goals_long',
    'habit': 'habits',
    'habits': 'habits',
    'strength': 'strengths',
    'strengths': 'strengths',
    'weakness': 'weaknesses',
    'weaknesses': 'weaknesses',
    'more': 'do_more_of',
    'do_more': 'do_more_of',
    'do_more_of': 'do_more_of',
    'do-more': 'do_more_of',
    'do-more-of': 'do_more_of',
    'less': 'do_less_of',
    'do_less': 'do_less_of',
    'do_less_of': 'do_less_of',
    'do-less': 'do_less_of',
    'do-less-of': 'do_less_of',
    'note': 'notes',
    'notes': 'notes',
}


def normalize_tag(tag: str) -> str:
    """Normalize tag: lowercase, replace - with _."""
    return tag.lower().replace('-', '_')


def parse_tagged_line(line: str) -> Optional[tuple[str, str, str]]:
    """
    Parse a tagged line.
    Returns (field, payload, original_tag) if valid tag found, None otherwise.

    Format: optional whitespace + # + tag + optional whitespace + payload
    """
    line = line.strip()
    if not line.startswith('#'):
        return None

    # Extract tag and payload
    match = re.match(r'^#(\S+)\s*(.*)', line)
    if not match:
        return None

    tag = match.group(1)
    payload = match.group(2).strip()

    # Normalize and lookup
    normalized_tag = normalize_tag(tag)
    field = TAG_MAP.get(normalized_tag)

    if field:
        return (field, payload, tag)
    else:
        return None


class TaggedLineResult:
    """Result of parsing tagged lines."""

    def __init__(self):
        self.known_proposals = []  # (field, text, line) for known tags
        self.unknown_lines = []  # (tag, line) for unknown tags
        self.untagged_lines = []  # plain lines without tags


def extract_tagged_lines(message: str) -> TaggedLineResult:
    """
    Extract tagged lines from message.

    Returns TaggedLineResult with:
    - known_proposals: list of (field, text, original_line) for known tags
    - unknown_lines: list of (tag, original_line) for unknown tags
    - untagged_lines: list of lines without tags
    """
    result = TaggedLineResult()
    lines = message.split('\n')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        parsed = parse_tagged_line(stripped)

        if parsed:
            field, payload, original_tag = parsed
            result.known_proposals.append((field, payload, stripped))
        elif stripped.startswith('#'):
            # Unknown tag
            match = re.match(r'^#(\S+)', stripped)
            if match:
                tag = match.group(1)
                result.unknown_lines.append((tag, stripped))
            else:
                result.untagged_lines.append(stripped)
        else:
            # Untagged line
            result.untagged_lines.append(stripped)

    return result
