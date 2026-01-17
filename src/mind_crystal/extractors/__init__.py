"""Extractors for tags and heuristics."""

from .tags import extract_tagged_lines, TAG_MAP
from .heuristics import extract_heuristics

__all__ = ['extract_tagged_lines', 'extract_heuristics', 'TAG_MAP']
