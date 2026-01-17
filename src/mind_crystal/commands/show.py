"""Show crystal state."""

from ..util import Storage


def cmd_show(data_dir: str = "./data", context: str = None):
    """Display crystal state summary."""
    storage = Storage(data_dir)

    try:
        state = storage.load_state_with_snapshot()
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Display summary
    print("=== Mind Crystal ===")
    if state.display_name:
        print(f"Name: {state.display_name}")
    if state.pronouns:
        print(f"Pronouns: {state.pronouns}")
    if state.one_liner:
        print(f"{state.one_liner}")
    print()

    # Helper to print list field
    def print_list(label: str, items: list[str], limit: int = 10):
        if items:
            print(f"{label} ({len(items)}):")
            for item in items[:limit]:
                print(f"  • {item}")
            if len(items) > limit:
                print(f"  ... and {len(items) - limit} more")
            print()

    # Key lists
    print_list("Values", state.values)
    print_list("Non-Negotiables", state.non_negotiables)
    print_list("Boundaries", state.boundaries)
    print_list("Needs", state.needs)
    print_list("Current Goals", state.goals_now)
    print_list("Strengths", state.strengths)
    print_list("Do More Of", state.do_more_of)
    print_list("Do Less Of", state.do_less_of)

    # Beams
    beams = state.beams
    if context:
        beams = [b for b in beams if b.contexts and context in b.contexts]

    active_beams = [b for b in beams if b.status == 'active']
    if active_beams:
        print(f"Active Beams ({len(active_beams)}):")
        for beam in active_beams[:10]:
            heat_str = f" [heat:{beam.heat}]" if beam.heat else ""
            ctx_str = f" [{','.join(beam.contexts)}]" if beam.contexts else ""
            print(f"  {beam.id}: {beam.claim}{heat_str}{ctx_str}")
        if len(active_beams) > 10:
            print(f"  ... and {len(active_beams) - 10} more")
        print()

    # Notes (limited)
    if state.notes:
        print(f"Notes ({len(state.notes)}):")
        for note in state.notes[-5:]:
            print(f"  • {note[:80]}{'...' if len(note) > 80 else ''}")
        print()
