"""Supersede a beam with new claim."""

from ..util import Storage
from ..events import create_event


def cmd_supersede(beam_id: str, new_claim: str, data_dir: str = "./data"):
    """Supersede an existing beam with a new claim."""
    storage = Storage(data_dir)

    with storage.lock():
        try:
            state = storage.load_state_with_snapshot()
        except ValueError as e:
            print(f"Error: {e}")
            return

        old_beam = state.get_beam(beam_id)
        if not old_beam:
            print(f"Beam {beam_id} not found")
            return

        print(f"Superseding beam {beam_id}:")
        print(f"  Old: {old_beam.claim}")
        print(f"  New: {new_claim}")
        confirm = input("Confirm? (y/n): ").strip().lower()

        if confirm != 'y':
            print("Cancelled")
            return

        event = create_event(
            'SUPERSEDE_BEAM',
            {
                'old_id': beam_id,
                'new_claim': new_claim,
                'source': '/supersede',
                'confidence': 'user_confirmed',
                'copy_meta': True
            }
        )
        storage.append_event(event)

        # Update snapshot
        events = storage.read_events()
        from ..events import replay_events
        state = replay_events(events)
        storage.write_snapshot(state, len(events) - 1)

        new_beam = state.beams[-1]
        print(f"Created {new_beam.id}")
