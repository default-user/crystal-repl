"""Initialize crystal data directory."""

from datetime import datetime, timezone

from ..util import Storage
from ..events import create_event


def cmd_init(data_dir: str = "./data"):
    """Initialize the crystal ledger."""
    storage = Storage(data_dir)
    storage.init()

    with storage.lock():
        if storage.events_path.exists():
            print(f"Crystal already initialized at {data_dir}")
            return

        # Create INIT event
        now = datetime.now(timezone.utc).isoformat()
        init_event = create_event(
            'INIT',
            {
                'schema_version': 'mind_crystal.v1',
                'created_at': now
            }
        )

        storage.append_event(init_event)

        # Create initial snapshot
        from ..events import replay_events
        events = storage.read_events()
        state = replay_events(events)
        storage.write_snapshot(state, len(events) - 1)

        print(f"Crystal initialized at {data_dir}")
