"""Utility functions."""

import json
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone

from .model import CrystalState
from .events import replay_events, EventApplier


class DataLock:
    """Simple file-based lock for single-process enforcement."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path

    def __enter__(self):
        if self.lock_path.exists():
            raise RuntimeError(
                "Lock file exists. Another crystal process may be running. "
                f"If not, delete {self.lock_path}"
            )
        self.lock_path.write_text(str(os.getpid()))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_path.exists():
            self.lock_path.unlink()


class Storage:
    """Handles event log and snapshot storage."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.events_path = self.data_dir / "events.jsonl"
        self.snapshot_path = self.data_dir / "snapshot.json"
        self.lock_path = self.data_dir / "lock"

    def init(self) -> None:
        """Initialize data directory."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def lock(self) -> DataLock:
        """Acquire lock for exclusive access."""
        return DataLock(self.lock_path)

    def append_event(self, event: dict[str, Any]) -> None:
        """Append event to event log."""
        with open(self.events_path, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def read_events(self) -> list[dict[str, Any]]:
        """Read all events from event log."""
        if not self.events_path.exists():
            return []

        events = []
        with open(self.events_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Malformed event at line {line_num}: {e}")

        return events

    def compute_events_hash(self) -> str:
        """Compute SHA256 hash of events file."""
        if not self.events_path.exists():
            return ""
        return hashlib.sha256(self.events_path.read_bytes()).hexdigest()

    def write_snapshot(self, state: CrystalState, last_event_index: int) -> None:
        """Write snapshot atomically."""
        snapshot = {
            'state': state.to_dict(),
            'last_event_index': last_event_index,
            'snapshot_ts': datetime.now(timezone.utc).isoformat(),
            'events_hash': self.compute_events_hash()
        }

        # Atomic write via temp file
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, suffix='.tmp')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(snapshot, f, indent=2)
            # Atomic replace
            os.replace(temp_path, self.snapshot_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def read_snapshot(self) -> Optional[dict[str, Any]]:
        """Read snapshot if it exists."""
        if not self.snapshot_path.exists():
            return None

        try:
            with open(self.snapshot_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed snapshot: {e}")

    def load_state(self) -> CrystalState:
        """Load current state by replaying events or loading snapshot."""
        events = self.read_events()
        if not events:
            raise ValueError("No events found. Run 'crystal init' first.")

        # For now, always replay from scratch for determinism
        # In production, could optimize with snapshots + incremental replay
        state = replay_events(events)
        return state

    def load_state_with_snapshot(self) -> CrystalState:
        """Load state using snapshot if available, otherwise full replay."""
        events = self.read_events()
        if not events:
            raise ValueError("No events found. Run 'crystal init' first.")

        snapshot = self.read_snapshot()
        if snapshot:
            # Validate snapshot integrity
            if snapshot['events_hash'] != self.compute_events_hash():
                # Hash mismatch, do full replay
                return replay_events(events)

            # Load from snapshot and apply remaining events
            state = CrystalState.from_dict(snapshot['state'])
            last_index = snapshot['last_event_index']

            if last_index < len(events) - 1:
                # Apply remaining events
                applier = EventApplier()
                # Restore beam counter from state
                if state.beams:
                    max_id = max(int(b.id[1:]) for b in state.beams)
                    applier.beam_counter = max_id

                for event in events[last_index + 1:]:
                    applier.apply_event(state, event)

            state.validate()
            return state
        else:
            # No snapshot, full replay
            return replay_events(events)
