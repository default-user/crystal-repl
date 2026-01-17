"""Tests for tag parsing."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mind_crystal.extractors.tags import extract_tagged_lines, parse_tagged_line


def test_leading_whitespace():
    """Test that leading whitespace before # is handled."""
    line = "  #value integrity"
    field, payload, tag = parse_tagged_line(line)
    assert field == 'values'
    assert payload == 'integrity'


def test_empty_payload():
    """Test that empty payload tags are detected."""
    line = "#need"
    field, payload, tag = parse_tagged_line(line)
    assert field == 'needs'
    assert payload == ''


def test_multiple_tagged_lines():
    """Test multiple tagged lines in one message."""
    message = """#value honesty
#boundary no gossip
#goal finish project"""

    result = extract_tagged_lines(message)
    assert len(result.known_proposals) == 3
    assert result.known_proposals[0][0] == 'values'
    assert result.known_proposals[1][0] == 'boundaries'
    assert result.known_proposals[2][0] == 'goals_now'


def test_unknown_tags_line_by_line():
    """Test that unknown tags are handled per line, not affecting known tags."""
    message = """#value trust
#foobar some unknown tag
#need rest"""

    result = extract_tagged_lines(message)

    # Known tags should still be extracted
    assert len(result.known_proposals) == 2
    assert result.known_proposals[0][0] == 'values'
    assert result.known_proposals[1][0] == 'needs'

    # Unknown tag should be flagged
    assert len(result.unknown_lines) == 1
    assert result.unknown_lines[0][0] == 'foobar'


def test_tag_normalization():
    """Test that tags with dashes are normalized to underscores."""
    line = "#do-more-of exercise"
    field, payload, tag = parse_tagged_line(line)
    assert field == 'do_more_of'
    assert payload == 'exercise'


def test_mixed_content():
    """Test message with tagged and untagged lines."""
    message = """This is untagged
#value clarity
Another untagged line
#goal learn Python"""

    result = extract_tagged_lines(message)
    assert len(result.known_proposals) == 2
    assert len(result.untagged_lines) == 2


if __name__ == '__main__':
    test_leading_whitespace()
    test_empty_payload()
    test_multiple_tagged_lines()
    test_unknown_tags_line_by_line()
    test_tag_normalization()
    test_mixed_content()
    print("All tag tests passed!")
