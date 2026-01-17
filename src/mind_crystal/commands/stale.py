"""Show stale beams due for review."""

from datetime import datetime, timedelta, timezone
from ..util import Storage


def cmd_stale(months: int = 6, data_dir: str = "./data"):
    """Show beams due for review."""
    storage = Storage(data_dir)

    try:
        state = storage.load_state_with_snapshot()
    except ValueError as e:
        print(f"Error: {e}")
        return

    today = datetime.now(timezone.utc).date()
    threshold_date = today - timedelta(days=months * 30)

    stale_beams = []

    for beam in state.beams:
        if beam.status != 'active':
            continue

        # Check review_after
        if beam.review_after:
            review_date = datetime.fromisoformat(beam.review_after).date()
            if review_date <= today:
                stale_beams.append((beam, f"review_after: {beam.review_after}"))
                continue

        # Check age based on beam date
        beam_date = datetime.fromisoformat(beam.date).date()
        if beam_date <= threshold_date:
            stale_beams.append((beam, f"age: {(today - beam_date).days} days"))

    if not stale_beams:
        print(f"No stale beams (threshold: {months} months)")
        return

    print(f"=== Stale Beams ({len(stale_beams)}) ===")
    print()
    for beam, reason in stale_beams:
        print(f"{beam.id} [{reason}]")
        print(f"  {beam.claim}")
        if beam.heat:
            print(f"  Heat: {beam.heat}")
        print()
