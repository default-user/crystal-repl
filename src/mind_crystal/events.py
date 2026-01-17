"""Event system for deterministic state replay."""

import json
from typing import Any
from datetime import datetime, timezone, date

from .model import CrystalState, Beam


class EventApplier:
    """Applies events to crystal state deterministically."""

    def __init__(self):
        self.beam_counter = 0

    def reset_counter(self):
        """Reset beam counter (for replay from scratch)."""
        self.beam_counter = 0

    def next_beam_id(self) -> str:
        """Generate next beam ID deterministically."""
        self.beam_counter += 1
        return f"B{self.beam_counter:04d}"

    def apply_event(self, state: CrystalState, event: dict[str, Any]) -> None:
        """Apply a single event to state. Mutates state in place."""
        event_type = event['type']
        payload = event['payload']
        ts = event['ts']

        if event_type == 'INIT':
            # Already initialized, just update timestamp
            state.updated_at = ts
            # Apply initial fields if present
            initial = payload.get('initial', {})
            for key, value in initial.items():
                if hasattr(state, key):
                    setattr(state, key, value)

        elif event_type == 'SET_FIELD':
            field = payload['field']
            value = payload['value']
            if not hasattr(state, field):
                raise ValueError(f"Unknown field: {field}")
            setattr(state, field, value)
            state.updated_at = ts

        elif event_type == 'SET_LIST_FIELD':
            field = payload['field']
            value = payload['value']
            if not hasattr(state, field):
                raise ValueError(f"Unknown field: {field}")
            setattr(state, field, value[:])  # Copy list
            state.updated_at = ts

        elif event_type == 'ADD_ITEM':
            field = payload['field']
            item = payload['item']
            if not hasattr(state, field):
                raise ValueError(f"Unknown field: {field}")
            state.add_item_dedupe(field, item)
            state.updated_at = ts

        elif event_type == 'REMOVE_ITEM':
            field = payload['field']
            item = payload['item']
            items = getattr(state, field, [])
            normalized = state.normalize_item(item)
            # Remove all matching items (normalized)
            new_items = [i for i in items if state.normalize_item(i) != normalized]
            setattr(state, field, new_items)
            state.updated_at = ts

        elif event_type == 'ADD_NOTE':
            note = payload['note']
            state.notes.append(note)
            state.updated_at = ts

        elif event_type == 'ADD_BEAM':
            beam_id = self.next_beam_id()
            today = datetime.fromisoformat(ts).date().isoformat()
            beam = Beam(
                id=beam_id,
                date=today,
                ts=ts,
                claim=payload['claim'],
                source=payload['source'][:240],  # Truncate
                confidence=payload.get('confidence', 'user_confirmed'),
                status='active',
                heat=payload.get('heat'),
                review_after=payload.get('review_after'),
                contexts=payload.get('contexts')
            )
            state.beams.append(beam)
            state.updated_at = ts

        elif event_type == 'SUPERSEDE_BEAM':
            old_id = payload['old_id']
            old_beam = state.get_beam(old_id)
            if not old_beam:
                raise ValueError(f"Beam {old_id} not found")

            # Create new beam
            new_beam_id = self.next_beam_id()
            today = datetime.fromisoformat(ts).date().isoformat()

            # Handle metadata copying
            copy_meta = payload.get('copy_meta', True)
            overrides = payload.get('overrides', {})

            if copy_meta:
                heat = overrides.get('heat', old_beam.heat)
                review_after = overrides.get('review_after', old_beam.review_after)
                contexts = overrides.get('contexts', old_beam.contexts)
            else:
                heat = overrides.get('heat')
                review_after = overrides.get('review_after')
                contexts = overrides.get('contexts')

            new_beam = Beam(
                id=new_beam_id,
                date=today,
                ts=ts,
                claim=payload['new_claim'],
                source=payload['source'][:240],
                confidence=payload.get('confidence', 'user_confirmed'),
                status='active',
                supersedes=old_id,
                heat=heat,
                review_after=review_after,
                contexts=contexts
            )

            # Update old beam
            old_beam.status = 'superseded'
            old_beam.superseded_by = new_beam_id

            state.beams.append(new_beam)
            state.updated_at = ts

        elif event_type == 'SET_BEAM_META':
            beam_id = payload['id']
            beam = state.get_beam(beam_id)
            if not beam:
                raise ValueError(f"Beam {beam_id} not found")

            if 'heat' in payload:
                beam.heat = payload['heat']
            if 'review_after' in payload:
                beam.review_after = payload['review_after']
            if 'contexts' in payload:
                beam.contexts = payload['contexts']
            if 'status' in payload:
                # Only allow retirement
                if payload['status'] == 'retired':
                    beam.status = 'retired'
                else:
                    raise ValueError(f"Cannot set status to {payload['status']} via SET_BEAM_META")

            state.updated_at = ts

        elif event_type == 'ADD_CONTEXT':
            name = payload['name']
            meta = payload.get('meta', {})
            state.contexts[name] = meta
            state.updated_at = ts

        else:
            raise ValueError(f"Unknown event type: {event_type}")


def create_event(event_type: str, payload: dict[str, Any], meta: dict[str, Any] = None) -> dict[str, Any]:
    """Create an event with standard structure."""
    return {
        'v': 1,
        'type': event_type,
        'ts': datetime.now(timezone.utc).isoformat(),
        'payload': payload,
        'meta': meta or {}
    }


def replay_events(events: list[dict[str, Any]]) -> CrystalState:
    """Replay events from scratch to rebuild state."""
    if not events:
        raise ValueError("No events to replay")

    first_event = events[0]
    if first_event['type'] != 'INIT':
        raise ValueError("First event must be INIT")

    # Create initial state
    state = CrystalState(
        schema_version=first_event['payload']['schema_version'],
        created_at=first_event['payload']['created_at'],
        updated_at=first_event['ts']
    )

    # Apply all events
    applier = EventApplier()
    for event in events:
        applier.apply_event(state, event)

    # Validate final state
    state.validate()

    return state
