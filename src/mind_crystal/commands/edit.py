"""Edit crystal fields."""

from ..util import Storage
from ..events import create_event


SCALAR_FIELDS = ['display_name', 'pronouns', 'one_liner', 'preferred_tone']
LIST_FIELDS = [
    'values', 'non_negotiables', 'boundaries', 'needs', 'fears',
    'goals_now', 'goals_long', 'habits', 'strengths', 'weaknesses',
    'do_more_of', 'do_less_of', 'notes', 'preferred_style'
]


def cmd_edit(field: str, data_dir: str = "./data"):
    """Interactive edit of a field."""
    storage = Storage(data_dir)

    if field not in SCALAR_FIELDS and field not in LIST_FIELDS:
        print(f"Unknown field: {field}")
        return

    with storage.lock():
        try:
            state = storage.load_state_with_snapshot()
        except ValueError as e:
            print(f"Error: {e}")
            return

        if field in SCALAR_FIELDS:
            # Edit scalar field
            current = getattr(state, field, "")
            print(f"Current value: {current}")
            print("Enter new value (or blank to clear):")
            new_value = input("> ").strip()

            event = create_event('SET_FIELD', {'field': field, 'value': new_value})
            storage.append_event(event)
            print(f"Updated {field}")

        else:
            # Edit list field
            items = getattr(state, field, [])
            print(f"{field} ({len(items)} items):")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item}")
            print()
            print("Commands: add <text> | remove <number> | clear")
            cmd = input("> ").strip()

            if cmd.startswith("add "):
                text = cmd[4:].strip()
                event = create_event('ADD_ITEM', {'field': field, 'item': text})
                storage.append_event(event)
                print(f"Added to {field}")

            elif cmd.startswith("remove "):
                try:
                    idx = int(cmd[7:].strip()) - 1
                    if 0 <= idx < len(items):
                        item = items[idx]
                        event = create_event('REMOVE_ITEM', {'field': field, 'item': item})
                        storage.append_event(event)
                        print(f"Removed from {field}")
                    else:
                        print("Invalid index")
                except ValueError:
                    print("Invalid number")

            elif cmd == "clear":
                confirm = input("Clear all items? (y/n): ").strip().lower()
                if confirm == 'y':
                    event = create_event('SET_LIST_FIELD', {'field': field, 'value': []})
                    storage.append_event(event)
                    print(f"Cleared {field}")
            else:
                print("Unknown command")

        # Update snapshot
        events = storage.read_events()
        from ..events import replay_events
        state = replay_events(events)
        storage.write_snapshot(state, len(events) - 1)
