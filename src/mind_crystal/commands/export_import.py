"""Export and import crystal state."""

import json
from datetime import datetime, timezone

from ..util import Storage
from ..events import create_event


def cmd_export(output_path: str, data_dir: str = "./data"):
    """Export crystal state to JSON."""
    storage = Storage(data_dir)

    try:
        state = storage.load_state_with_snapshot()
    except ValueError as e:
        print(f"Error: {e}")
        return

    with open(output_path, 'w') as f:
        json.dump(state.to_dict(), f, indent=2)

    print(f"Exported to {output_path}")


def cmd_import(input_path: str, data_dir: str = "./data"):
    """Import crystal state from JSON."""
    storage = Storage(data_dir)

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading file: {e}")
        return

    with storage.lock():
        # Create INIT event with imported data
        now = datetime.now(timezone.utc).isoformat()

        # Extract and create INIT
        init_event = create_event(
            'INIT',
            {
                'schema_version': data.get('schema_version', 'mind_crystal.v1'),
                'created_at': data.get('created_at', now),
                'initial': {
                    'display_name': data.get('display_name', ''),
                    'pronouns': data.get('pronouns', ''),
                    'one_liner': data.get('one_liner', ''),
                    'preferred_tone': data.get('preferred_tone', 'direct'),
                    'preferred_style': data.get('preferred_style', ['structured', 'truth-marked', 'no-fluff'])
                }
            }
        )
        storage.append_event(init_event)

        # Import list fields
        list_fields = [
            'values', 'non_negotiables', 'boundaries', 'needs', 'fears',
            'goals_now', 'goals_long', 'habits', 'strengths', 'weaknesses',
            'do_more_of', 'do_less_of', 'notes'
        ]

        for field in list_fields:
            if field in data and data[field]:
                for item in data[field]:
                    event = create_event('ADD_ITEM', {'field': field, 'item': item})
                    storage.append_event(event)

        # Import contexts
        contexts = data.get('contexts', {})
        for name, meta in contexts.items():
            event = create_event('ADD_CONTEXT', {'name': name, 'meta': meta})
            storage.append_event(event)

        # Import beams
        beams = data.get('beams', [])
        for beam_data in beams:
            if beam_data.get('status') == 'active' and not beam_data.get('supersedes'):
                # Only import original active beams; superseded ones will be recreated via SUPERSEDE events
                event = create_event(
                    'ADD_BEAM',
                    {
                        'claim': beam_data['claim'],
                        'source': beam_data.get('source', 'import'),
                        'confidence': beam_data.get('confidence', 'user_confirmed'),
                        'heat': beam_data.get('heat'),
                        'review_after': beam_data.get('review_after'),
                        'contexts': beam_data.get('contexts')
                    }
                )
                storage.append_event(event)

        # Update snapshot
        events = storage.read_events()
        from ..events import replay_events
        state = replay_events(events)
        storage.write_snapshot(state, len(events) - 1)

        print(f"Imported from {input_path}")
