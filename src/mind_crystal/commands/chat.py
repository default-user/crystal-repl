"""Interactive REPL chat for building crystal."""

from ..util import Storage
from ..events import create_event
from ..extractors import extract_tagged_lines, extract_heuristics


ALLOWED_BUCKETS = [
    'values', 'boundary', 'need', 'fear', 'goal_now', 'goal_long',
    'habit', 'strength', 'weakness', 'note'
]

BUCKET_TO_FIELD = {
    'values': 'values',
    'boundary': 'boundaries',
    'need': 'needs',
    'fear': 'fears',
    'goal_now': 'goals_now',
    'goal_long': 'goals_long',
    'habit': 'habits',
    'strength': 'strengths',
    'weakness': 'weaknesses',
    'note': 'notes'
}


def get_user_input() -> str:
    """Get multi-line input from user."""
    print("You> (blank line to submit, Ctrl-D to exit)")
    lines = []
    try:
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
    except EOFError:
        return None

    return '\n'.join(lines)


def ask_yn(prompt: str) -> bool:
    """Ask yes/no question."""
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False


def bucket_prompt(line: str) -> tuple[str, str]:
    """
    Hand off to user to pick a bucket.
    Returns (field, text) or (None, None) if cancelled.
    """
    print(f"\nKai> I didn't find clean category matches. Pick a bucket:")
    print(f"  {' | '.join(ALLOWED_BUCKETS)}")
    bucket = input("> ").strip().lower()

    if bucket not in BUCKET_TO_FIELD:
        print(f"Unknown bucket: {bucket}")
        return None, None

    field = BUCKET_TO_FIELD[bucket]
    return field, line


def process_message(message: str, storage: Storage) -> None:
    """Process a single user message."""
    if not message or not message.strip():
        return

    # Extract tagged lines
    result = extract_tagged_lines(message)

    events_to_write = []
    any_processed = False

    # Process known tag proposals
    for field, payload, original_line in result.known_proposals:
        any_processed = True

        # Check for empty payload (needs bucket prompt)
        if not payload:
            print(f"\nKai> Found #{field} tag with no text.")
            print(f"  Line: {original_line}")
            field_resolved, text = bucket_prompt(original_line)
            if not field_resolved:
                continue
            field = field_resolved
            payload = text
        else:
            # Ask for confirmation
            print(f"\nKai> Add to {field}?")
            print(f"  {payload}")
            if not ask_yn("Confirm"):
                continue

        # Add item event
        events_to_write.append(create_event('ADD_ITEM', {'field': field, 'item': payload}))

        # Add beam event
        claim = f"{field}: {payload}"
        events_to_write.append(create_event(
            'ADD_BEAM',
            {
                'claim': claim,
                'source': original_line[:240],
                'confidence': 'user_confirmed'
            }
        ))

    # Process unknown tag lines
    for tag, line in result.unknown_lines:
        any_processed = True
        print(f"\nKai> Unknown tag '#{tag}'.")
        print(f"  Line: {line}")
        if ask_yn("Treat this line as note"):
            events_to_write.append(create_event('ADD_NOTE', {'note': line}))
        else:
            # Bucket prompt
            field, text = bucket_prompt(line)
            if field:
                events_to_write.append(create_event('ADD_ITEM', {'field': field, 'item': text}))
                claim = f"{field}: {text}"
                events_to_write.append(create_event(
                    'ADD_BEAM',
                    {
                        'claim': claim,
                        'source': line[:240],
                        'confidence': 'user_confirmed'
                    }
                ))

    # If no known proposals and no unknown tags, try heuristics
    if not result.known_proposals and not result.unknown_lines:
        # Run heuristics on full message
        heuristic_proposals = extract_heuristics(message)

        if heuristic_proposals:
            for field, suggestion in heuristic_proposals:
                any_processed = True
                print(f"\nKai> Heuristic suggestion for {field}:")
                print(f"  {suggestion[:200]}{'...' if len(suggestion) > 200 else ''}")
                if ask_yn("Add this"):
                    events_to_write.append(create_event('ADD_ITEM', {'field': field, 'item': suggestion}))
                    claim = f"{field}: {suggestion}"
                    events_to_write.append(create_event(
                        'ADD_BEAM',
                        {
                            'claim': claim,
                            'source': message[:240],
                            'confidence': 'heuristic_confirmed'
                        }
                    ))

    # If still nothing processed, bucket prompt for untagged lines
    if not any_processed and result.untagged_lines:
        # Use full message for bucket prompt
        field, text = bucket_prompt(message)
        if field:
            events_to_write.append(create_event('ADD_ITEM', {'field': field, 'item': text}))
            claim = f"{field}: {text}"
            events_to_write.append(create_event(
                'ADD_BEAM',
                {
                    'claim': claim,
                    'source': message[:240],
                    'confidence': 'user_confirmed'
                }
            ))
            any_processed = True

    # Write all events
    if events_to_write:
        with storage.lock():
            for event in events_to_write:
                storage.append_event(event)

            # Update snapshot
            events = storage.read_events()
            from ..events import replay_events
            state = replay_events(events)
            storage.write_snapshot(state, len(events) - 1)

        print("\nKai> Recorded.")
    elif any_processed:
        print("\nKai> Nothing recorded.")


def cmd_chat(data_dir: str = "./data"):
    """Start interactive REPL chat."""
    storage = Storage(data_dir)

    try:
        state = storage.load_state_with_snapshot()
    except ValueError as e:
        print(f"Error: {e}")
        return

    print("=== Mind Crystal Chat ===")
    print("Multi-line input supported. Blank line to submit. Ctrl-D to exit.")
    print()

    while True:
        message = get_user_input()
        if message is None:
            print("\nKai> Goodbye.")
            break

        process_message(message, storage)
        print()
