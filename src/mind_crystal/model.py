"""Core data models for Mind Crystal Ledger."""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime


@dataclass
class Beam:
    """A beam represents a structured claim/assertion with metadata."""
    id: str
    date: str  # YYYY-MM-DD
    ts: str  # ISO8601 UTC
    claim: str
    source: str  # max 240 chars
    confidence: str = "user_confirmed"
    status: str = "active"  # active | superseded | retired
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    heat: Optional[int] = None
    review_after: Optional[str] = None  # YYYY-MM-DD
    contexts: Optional[list[str]] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Beam":
        """Create Beam from dict."""
        return Beam(**d)


@dataclass
class CrystalState:
    """The complete mind crystal state."""
    schema_version: str = "mind_crystal.v1"
    created_at: str = ""
    updated_at: str = ""
    display_name: str = ""
    pronouns: str = ""
    one_liner: str = ""
    preferred_tone: str = "direct"
    preferred_style: list[str] = field(default_factory=lambda: ["structured", "truth-marked", "no-fluff"])

    # Lists
    values: list[str] = field(default_factory=list)
    non_negotiables: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    fears: list[str] = field(default_factory=list)
    goals_now: list[str] = field(default_factory=list)
    goals_long: list[str] = field(default_factory=list)
    habits: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    do_more_of: list[str] = field(default_factory=list)
    do_less_of: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    # Contexts
    contexts: dict[str, dict] = field(default_factory=dict)

    # Beams
    beams: list[Beam] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        d = asdict(self)
        d['beams'] = [b.to_dict() for b in self.beams]
        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "CrystalState":
        """Create CrystalState from dict."""
        beams_data = d.pop('beams', [])
        state = CrystalState(**d)
        state.beams = [Beam.from_dict(b) for b in beams_data]
        return state

    def validate(self) -> None:
        """Validate state invariants."""
        if self.schema_version != "mind_crystal.v1":
            raise ValueError(f"Invalid schema version: {self.schema_version}")

        # Check beam ID uniqueness
        beam_ids = [b.id for b in self.beams]
        if len(beam_ids) != len(set(beam_ids)):
            raise ValueError("Duplicate beam IDs found")

        # Check supersede relationships
        beam_map = {b.id: b for b in self.beams}
        for beam in self.beams:
            if beam.status == "superseded":
                if not beam.superseded_by:
                    raise ValueError(f"Beam {beam.id} is superseded but has no superseded_by")
                if beam.superseded_by not in beam_map:
                    raise ValueError(f"Beam {beam.id} superseded_by points to non-existent beam {beam.superseded_by}")

            if beam.supersedes:
                if beam.supersedes not in beam_map:
                    raise ValueError(f"Beam {beam.id} supersedes non-existent beam {beam.supersedes}")
                old_beam = beam_map[beam.supersedes]
                if old_beam.superseded_by != beam.id:
                    raise ValueError(f"Beam {beam.id} supersedes {beam.supersedes} but link is not bidirectional")

    def get_beam(self, beam_id: str) -> Optional[Beam]:
        """Get beam by ID."""
        for beam in self.beams:
            if beam.id == beam_id:
                return beam
        return None

    def normalize_item(self, item: str) -> str:
        """Normalize item for deduplication (case/whitespace insensitive)."""
        return item.strip().lower()

    def has_item(self, field: str, item: str) -> bool:
        """Check if item exists in field (case/whitespace insensitive)."""
        items = getattr(self, field, [])
        normalized = self.normalize_item(item)
        return any(self.normalize_item(i) == normalized for i in items)

    def add_item_dedupe(self, field: str, item: str) -> bool:
        """Add item to field if not already present. Returns True if added."""
        if self.has_item(field, item):
            return False
        items = getattr(self, field)
        items.append(item)
        return True
