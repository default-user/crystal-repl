"""Show supported tags."""

from ..extractors import TAG_MAP


def cmd_tags():
    """Display supported tag vocabulary."""
    print("=== Supported Tags ===")
    print()

    # Group by target field
    field_tags = {}
    for tag, field in TAG_MAP.items():
        if field not in field_tags:
            field_tags[field] = []
        field_tags[field].append(f"#{tag}")

    for field in sorted(field_tags.keys()):
        tags = sorted(set(field_tags[field]))
        print(f"{field}:")
        print(f"  {', '.join(tags)}")
        print()
