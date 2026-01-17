"""Tests for beam supersede logic."""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mind_crystal.events import create_event, replay_events


def test_supersede_linkage():
    """Test that supersede creates proper bidirectional links."""
    now = datetime.now(timezone.utc).isoformat()

    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
        create_event('ADD_BEAM', {'claim': 'original claim', 'source': 'test'}),
        create_event('SUPERSEDE_BEAM', {
            'old_id': 'B0001',
            'new_claim': 'updated claim',
            'source': 'test',
            'confidence': 'user_confirmed',
            'copy_meta': True
        }),
    ]

    state = replay_events(events)

    # Should have 2 beams
    assert len(state.beams) == 2

    old_beam = state.beams[0]
    new_beam = state.beams[1]

    # Old beam should be superseded
    assert old_beam.id == 'B0001'
    assert old_beam.status == 'superseded'
    assert old_beam.superseded_by == 'B0002'

    # New beam should be active and link back
    assert new_beam.id == 'B0002'
    assert new_beam.status == 'active'
    assert new_beam.supersedes == 'B0001'
    assert new_beam.claim == 'updated claim'


def test_supersede_meta_copy():
    """Test that supersede copies metadata when copy_meta=True."""
    now = datetime.now(timezone.utc).isoformat()

    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
        create_event('ADD_BEAM', {
            'claim': 'original',
            'source': 'test',
            'heat': 8,
            'contexts': ['work', 'home'],
            'review_after': '2025-12-31'
        }),
        create_event('SUPERSEDE_BEAM', {
            'old_id': 'B0001',
            'new_claim': 'updated',
            'source': 'test',
            'copy_meta': True
        }),
    ]

    state = replay_events(events)
    new_beam = state.beams[1]

    # Metadata should be copied
    assert new_beam.heat == 8
    assert new_beam.contexts == ['work', 'home']
    assert new_beam.review_after == '2025-12-31'


def test_supersede_meta_override():
    """Test that supersede can override metadata."""
    now = datetime.now(timezone.utc).isoformat()

    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
        create_event('ADD_BEAM', {
            'claim': 'original',
            'source': 'test',
            'heat': 5,
            'contexts': ['work']
        }),
        create_event('SUPERSEDE_BEAM', {
            'old_id': 'B0001',
            'new_claim': 'updated',
            'source': 'test',
            'copy_meta': True,
            'overrides': {
                'heat': 9,
                'contexts': ['personal']
            }
        }),
    ]

    state = replay_events(events)
    new_beam = state.beams[1]

    # Overridden metadata should be used
    assert new_beam.heat == 9
    assert new_beam.contexts == ['personal']


def test_supersede_validation():
    """Test that state validates supersede relationships."""
    now = datetime.now(timezone.utc).isoformat()

    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
        create_event('ADD_BEAM', {'claim': 'original', 'source': 'test'}),
        create_event('SUPERSEDE_BEAM', {
            'old_id': 'B0001',
            'new_claim': 'updated',
            'source': 'test'
        }),
    ]

    state = replay_events(events)

    # Validation should pass
    try:
        state.validate()
        validation_passed = True
    except Exception:
        validation_passed = False

    assert validation_passed


if __name__ == '__main__':
    test_supersede_linkage()
    test_supersede_meta_copy()
    test_supersede_meta_override()
    test_supersede_validation()
    print("All supersede tests passed!")
