"""Tests for stale beam detection."""

import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mind_crystal.events import create_event, replay_events


def test_stale_review_after():
    """Test that beams with past review_after are detected as stale."""
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=10)).date().isoformat()
    future_date = (now + timedelta(days=10)).date().isoformat()

    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now.isoformat()}),
        create_event('ADD_BEAM', {
            'claim': 'stale beam',
            'source': 'test',
            'review_after': past_date
        }),
        create_event('ADD_BEAM', {
            'claim': 'fresh beam',
            'source': 'test',
            'review_after': future_date
        }),
    ]

    state = replay_events(events)
    today = now.date()

    stale_beams = []
    for beam in state.beams:
        if beam.status == 'active' and beam.review_after:
            review_date = datetime.fromisoformat(beam.review_after).date()
            if review_date <= today:
                stale_beams.append(beam)

    assert len(stale_beams) == 1
    assert stale_beams[0].claim == 'stale beam'


def test_stale_by_age():
    """Test that old beams are detected as stale based on age."""
    now = datetime.now(timezone.utc)
    old_date = (now - timedelta(days=200)).date().isoformat()

    # Create beam with old date
    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now.isoformat()}),
    ]

    # Manually create old beam event with past timestamp
    old_ts = (now - timedelta(days=200)).isoformat()
    old_beam_event = {
        'v': 1,
        'type': 'ADD_BEAM',
        'ts': old_ts,
        'payload': {
            'claim': 'old beam',
            'source': 'test'
        },
        'meta': {}
    }
    events.append(old_beam_event)

    state = replay_events(events)

    # Check age (6 months = ~180 days)
    threshold_months = 6
    threshold_date = now.date() - timedelta(days=threshold_months * 30)

    stale_beams = []
    for beam in state.beams:
        if beam.status == 'active':
            beam_date = datetime.fromisoformat(beam.date).date()
            if beam_date <= threshold_date:
                stale_beams.append(beam)

    assert len(stale_beams) == 1
    assert stale_beams[0].claim == 'old beam'


def test_stale_ignores_superseded():
    """Test that superseded beams are not shown as stale (only active beams)."""
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=10)).date().isoformat()

    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now.isoformat()}),
        create_event('ADD_BEAM', {
            'claim': 'old beam',
            'source': 'test',
            'review_after': past_date
        }),
        create_event('SUPERSEDE_BEAM', {
            'old_id': 'B0001',
            'new_claim': 'updated beam',
            'source': 'test',
            'copy_meta': False  # Don't copy review_after
        }),
    ]

    state = replay_events(events)
    today = now.date()

    # Only check active beams
    stale_beams = []
    for beam in state.beams:
        if beam.status == 'active' and beam.review_after:
            review_date = datetime.fromisoformat(beam.review_after).date()
            if review_date <= today:
                stale_beams.append(beam)

    # The superseded beam should not appear (status != active)
    # The new beam has no review_after (copy_meta=False)
    assert len(stale_beams) == 0


def test_stale_mixed():
    """Test stale detection with mixed beam types."""
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=10)).date().isoformat()
    future_date = (now + timedelta(days=10)).date().isoformat()

    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now.isoformat()}),
        create_event('ADD_BEAM', {'claim': 'beam1', 'source': 'test', 'review_after': past_date}),
        create_event('ADD_BEAM', {'claim': 'beam2', 'source': 'test', 'review_after': future_date}),
        create_event('ADD_BEAM', {'claim': 'beam3', 'source': 'test'}),  # No review_after
    ]

    state = replay_events(events)
    today = now.date()

    stale_beams = []
    for beam in state.beams:
        if beam.status == 'active' and beam.review_after:
            review_date = datetime.fromisoformat(beam.review_after).date()
            if review_date <= today:
                stale_beams.append(beam)

    assert len(stale_beams) == 1
    assert stale_beams[0].claim == 'beam1'


if __name__ == '__main__':
    test_stale_review_after()
    test_stale_by_age()
    test_stale_ignores_superseded()
    test_stale_mixed()
    print("All stale tests passed!")
