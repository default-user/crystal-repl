# Mind Crystal Ledger v1.0

Local-first, event-sourced personal knowledge ledger with an honesty posture.

## What This Is

Mind Crystal Ledger is a CLI and REPL system for capturing and organizing structured personal data (values, goals, boundaries, etc.) with strict guarantees:

- **Local-only**: No network calls, no telemetry
- **Event-sourced**: Append-only event log ensures deterministic replay
- **Honesty posture**: Human-declared intent via tags is primary; heuristics are secondary and always confirmed
- **Fail-closed**: Malformed data causes clear errors, never silent best-effort fixes

## Core Principles

1. **Human-declared intent is primary**: Use `#tags` to explicitly categorize your thoughts
2. **Heuristics are secondary**: Only used when no tags found, and always require confirmation
3. **Deterministic replay**: Same events → same state, guaranteed
4. **No silent mutation**: Every state change emits an event
5. **Single-process**: File-based locking prevents concurrent modifications

## Installation

```bash
# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Initialize crystal ledger
crystal init

# Start interactive chat
crystal chat

# View current state
crystal show

# List supported tags
crystal tags
```

## Commands

### `crystal init`
Initialize the crystal ledger. Creates `./data` directory with event log and snapshot.

### `crystal chat`
Start interactive REPL for building your crystal.

**Tag syntax:**
```
#value honesty
#boundary no gossip
#goal finish the prototype
#need 8 hours of sleep
```

**Multi-line input**: Press Enter on blank line to submit. Ctrl-D to exit.

### `crystal show [--context NAME]`
Display crystal state summary. Use `--context` to filter beams by context.

### `crystal tags`
Display all supported tag vocabulary and field mappings.

### `crystal edit FIELD`
Interactive edit of a field (scalar or list).

**Example:**
```bash
crystal edit values
# Shows current values, prompts for add/remove/clear
```

### `crystal supersede BEAM_ID NEW_CLAIM`
Supersede an existing beam with updated claim. Creates bidirectional link.

**Example:**
```bash
crystal supersede B0001 "I value clarity over cleverness"
```

### `crystal stale [--months N]`
Show beams due for review (default: 6 months).

**Detection criteria:**
- Beams with `review_after` date in the past
- Beams older than N months

### `crystal export PATH`
Export current state to JSON file.

### `crystal import PATH`
Import state from JSON file. Writes events to reconstruct state.

## Tag Vocabulary

| Tags | Field |
|------|-------|
| #value, #values | values |
| #nonnegotiable, #non_negotiables | non_negotiables |
| #boundary, #boundaries | boundaries |
| #need, #needs | needs |
| #fear, #fears | fears |
| #goal, #goals | goals_now |
| #goal_now, #goals_now | goals_now |
| #goal_long, #goals_long | goals_long |
| #habit, #habits | habits |
| #strength, #strengths | strengths |
| #weakness, #weaknesses | weaknesses |
| #more, #do_more, #do_more_of | do_more_of |
| #less, #do_less, #do_less_of | do_less_of |
| #note, #notes | notes |

## File Formats

### Event Log (`./data/events.jsonl`)

Append-only, newline-delimited JSON. Each line is an event:

```json
{
  "v": 1,
  "type": "ADD_ITEM",
  "ts": "2025-01-17T12:00:00+00:00",
  "payload": {"field": "values", "item": "honesty"},
  "meta": {}
}
```

**Event Types:**
- `INIT`: Initialize crystal
- `SET_FIELD`: Set scalar field
- `SET_LIST_FIELD`: Replace list field
- `ADD_ITEM`: Add item to list
- `REMOVE_ITEM`: Remove item from list
- `ADD_NOTE`: Add note
- `ADD_BEAM`: Create beam
- `SUPERSEDE_BEAM`: Supersede beam
- `SET_BEAM_META`: Update beam metadata
- `ADD_CONTEXT`: Add context

### Snapshot (`./data/snapshot.json`)

Full state snapshot for performance:

```json
{
  "state": { /* CrystalState object */ },
  "last_event_index": 42,
  "snapshot_ts": "2025-01-17T12:00:00+00:00",
  "events_hash": "sha256..."
}
```

## Beams

**Beams** are structured claims with metadata:

- `id`: Unique identifier (B0001, B0002, ...)
- `claim`: The assertion text
- `source`: Where it came from (chat message, command)
- `confidence`: Level of certainty (user_confirmed, heuristic_confirmed)
- `status`: active | superseded | retired
- `heat`: Optional urgency/importance (0-10)
- `review_after`: Optional review date
- `contexts`: Optional list of contexts where this applies

**Supersede chains**: When a beam is superseded, bidirectional links are maintained:
- Old beam: `status=superseded`, `superseded_by=B0002`
- New beam: `status=active`, `supersedes=B0001`

## Recovery & Rollback

### Rebuild from events
```bash
# Delete snapshot to force full replay
rm ./data/snapshot.json
crystal show  # Triggers replay
```

### Rollback to previous state
```bash
# CAUTION: Manual event log editing
# 1. Back up events.jsonl
cp ./data/events.jsonl ./data/events.jsonl.backup

# 2. Truncate to desired event count (e.g., remove last 5 events)
head -n -5 ./data/events.jsonl > ./data/events.jsonl.tmp
mv ./data/events.jsonl.tmp ./data/events.jsonl

# 3. Delete snapshot and reload
rm ./data/snapshot.json
crystal show
```

### Verify integrity
```bash
# Export and reimport to verify round-trip
crystal export backup.json
rm -rf ./data
crystal init
crystal import backup.json
```

## Determinism Guarantee

**Same events in same order = same state**, always.

- Beam IDs assigned by event order, not timestamps
- No wall-clock dependencies during replay
- Snapshot hashes verify event log integrity

**Testing:**
```bash
python tests/test_replay.py  # Replay determinism tests
```

## Chat Flow

When you send a message to `crystal chat`:

1. **Parse tagged lines**: Extract known tags, unknown tags, untagged text
2. **Known tags**: Confirm each proposal, add to field + create beam
3. **Unknown tags**: Prompt to treat as note or pick bucket
4. **No tags + heuristics match**: Confirm heuristic suggestion
5. **Fallback**: Bucket prompt (pick category manually)

**Bucket prompt:**
```
Kai> I didn't find clean category matches. Pick a bucket:
  values | boundary | need | fear | goal_now | goal_long | habit | strength | weakness | note
```

## Non-Goals

- **Not a therapy tool**: Neutral prompts, no emotional coaching
- **Not a sync service**: Local-only, no cloud/network
- **Not schema-flexible**: v1.0 schema is fixed (migrations planned for future versions)
- **Not multi-process**: Single writer via file lock

## Example Session

```bash
$ crystal init
Crystal initialized at ./data

$ crystal chat
=== Mind Crystal Chat ===
Multi-line input supported. Blank line to submit. Ctrl-D to exit.

You> (blank line to submit, Ctrl-D to exit)
#value integrity in all communication
#goal ship the prototype by end of month

Kai> Add to values?
  integrity in all communication
Confirm? (y/n): y

Kai> Add to goals_now?
  ship the prototype by end of month
Confirm? (y/n): y

Kai> Recorded.

You> (blank line to submit, Ctrl-D to exit)
^D
Kai> Goodbye.

$ crystal show
=== Mind Crystal ===

Values (1):
  • integrity in all communication

Current Goals (1):
  • ship the prototype by end of month

Active Beams (2):
  B0001: values: integrity in all communication
  B0002: goals_now: ship the prototype by end of month
```

## Testing

```bash
# Run all tests
python tests/test_tags.py
python tests/test_replay.py
python tests/test_supersede.py
python tests/test_stale.py

# Or with pytest (if installed)
pytest tests/
```

## Data Directory Structure

```
./data/
├── events.jsonl    # Append-only event log
├── snapshot.json   # State snapshot
└── lock            # Process lock file
```

## License

MIT License - see LICENSE file

## Project Structure

```
mind_crystal_ledger/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/mind_crystal/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py           # CLI entry point
│   ├── model.py         # Data models
│   ├── events.py        # Event system
│   ├── util.py          # Storage & utilities
│   ├── extractors/
│   │   ├── tags.py      # Tag parsing
│   │   └── heuristics.py # Heuristic extraction
│   ├── commands/
│   │   ├── init.py
│   │   ├── chat.py
│   │   ├── show.py
│   │   ├── tags.py
│   │   ├── edit.py
│   │   ├── supersede.py
│   │   ├── stale.py
│   │   └── export_import.py
│   └── migrate/
│       └── v1_to_v1_1.py  # Future migrations
└── tests/
    ├── test_tags.py
    ├── test_replay.py
    ├── test_supersede.py
    └── test_stale.py
```
