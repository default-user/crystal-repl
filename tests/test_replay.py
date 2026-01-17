"""Tests for event replay determinism."""

import sys
import os
import tempfile
import shutil
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mind_crystal.events import create_event, replay_events
from mind_crystal.util import Storage


def test_replay_determinism():
    """Test that replaying same events produces identical state."""
    # Create events
    now = datetime.now(timezone.utc).isoformat()
    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
        create_event('ADD_ITEM', {'field': 'values', 'item': 'honesty'}),
        create_event('ADD_ITEM', {'field': 'goals_now', 'item': 'learn Python'}),
        create_event('ADD_BEAM', {'claim': 'test claim', 'source': 'test'}),
    ]

    # Replay twice
    state1 = replay_events(events)
    state2 = replay_events(events)

    # States should be identical
    assert state1.to_dict() == state2.to_dict()
    assert state1.values == state2.values == ['honesty']
    assert state1.goals_now == state2.goals_now == ['learn Python']
    assert len(state1.beams) == len(state2.beams) == 1
    assert state1.beams[0].id == state2.beams[0].id == 'B0001'


def test_beam_id_determinism():
    """Test that beam IDs are assigned deterministically by event order."""
    now = datetime.now(timezone.utc).isoformat()
    events = [
        create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
        create_event('ADD_BEAM', {'claim': 'first beam', 'source': 'test'}),
        create_event('ADD_BEAM', {'claim': 'second beam', 'source': 'test'}),
        create_event('ADD_BEAM', {'claim': 'third beam', 'source': 'test'}),
    ]

    state1 = replay_events(events)
    state2 = replay_events(events)

    # Beam IDs should match
    assert [b.id for b in state1.beams] == [b.id for b in state2.beams]
    assert [b.id for b in state1.beams] == ['B0001', 'B0002', 'B0003']


def test_snapshot_roundtrip():
    """Test that snapshot save/load preserves state."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()

    try:
        storage = Storage(temp_dir)
        storage.init()

        # Create events
        now = datetime.now(timezone.utc).isoformat()
        events = [
            create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
            create_event('ADD_ITEM', {'field': 'values', 'item': 'integrity'}),
            create_event('ADD_BEAM', {'claim': 'test beam', 'source': 'test'}),
        ]

        for event in events:
            storage.append_event(event)

        # Create state and snapshot
        state_original = replay_events(storage.read_events())
        storage.write_snapshot(state_original, len(events) - 1)

        # Load snapshot
        snapshot = storage.read_snapshot()
        assert snapshot is not None

        from mind_crystal.model import CrystalState
        state_loaded = CrystalState.from_dict(snapshot['state'])

        # States should match
        assert state_original.to_dict() == state_loaded.to_dict()

    finally:
        shutil.rmtree(temp_dir)


def test_full_storage_replay():
    """Test full replay from storage."""
    temp_dir = tempfile.mkdtemp()

    try:
        storage = Storage(temp_dir)
        storage.init()

        # Write events
        now = datetime.now(timezone.utc).isoformat()
        events = [
            create_event('INIT', {'schema_version': 'mind_crystal.v1', 'created_at': now}),
            create_event('ADD_ITEM', {'field': 'values', 'item': 'honesty'}),
            create_event('ADD_ITEM', {'field': 'values', 'item': 'clarity'}),
            create_event('ADD_BEAM', {'claim': 'beam 1', 'source': 'test'}),
            create_event('ADD_BEAM', {'claim': 'beam 2', 'source': 'test'}),
        ]

        for event in events:
            storage.append_event(event)

        # Load state
        state = storage.load_state()

        assert state.values == ['honesty', 'clarity']
        assert len(state.beams) == 2
        assert state.beams[0].id == 'B0001'
        assert state.beams[1].id == 'B0002'

    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    test_replay_determinism()
    test_beam_id_determinism()
    test_snapshot_roundtrip()
    test_full_storage_replay()
    print("All replay tests passed!")
