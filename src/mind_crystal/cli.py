"""CLI entry point for Mind Crystal Ledger."""

import argparse
import sys

from .commands.init import cmd_init
from .commands.show import cmd_show
from .commands.tags import cmd_tags
from .commands.edit import cmd_edit
from .commands.supersede import cmd_supersede
from .commands.stale import cmd_stale
from .commands.export_import import cmd_export, cmd_import
from .commands.chat import cmd_chat


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Mind Crystal Ledger - Local-first personal knowledge system"
    )
    parser.add_argument(
        '--data-dir',
        default='./data',
        help='Data directory path (default: ./data)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init
    subparsers.add_parser('init', help='Initialize crystal ledger')

    # chat
    subparsers.add_parser('chat', help='Start interactive REPL')

    # show
    show_parser = subparsers.add_parser('show', help='Show crystal state')
    show_parser.add_argument('--context', help='Filter by context')

    # tags
    subparsers.add_parser('tags', help='Show supported tags')

    # edit
    edit_parser = subparsers.add_parser('edit', help='Edit a field')
    edit_parser.add_argument('field', help='Field name to edit')

    # supersede
    supersede_parser = subparsers.add_parser('supersede', help='Supersede a beam')
    supersede_parser.add_argument('beam_id', help='Beam ID to supersede')
    supersede_parser.add_argument('new_claim', help='New claim text')

    # stale
    stale_parser = subparsers.add_parser('stale', help='Show stale beams')
    stale_parser.add_argument('--months', type=int, default=6, help='Age threshold in months')

    # export
    export_parser = subparsers.add_parser('export', help='Export state to JSON')
    export_parser.add_argument('path', help='Output file path')

    # import
    import_parser = subparsers.add_parser('import', help='Import state from JSON')
    import_parser.add_argument('path', help='Input file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'init':
            cmd_init(args.data_dir)
        elif args.command == 'chat':
            cmd_chat(args.data_dir)
        elif args.command == 'show':
            cmd_show(args.data_dir, args.context)
        elif args.command == 'tags':
            cmd_tags()
        elif args.command == 'edit':
            cmd_edit(args.field, args.data_dir)
        elif args.command == 'supersede':
            cmd_supersede(args.beam_id, args.new_claim, args.data_dir)
        elif args.command == 'stale':
            cmd_stale(args.months, args.data_dir)
        elif args.command == 'export':
            cmd_export(args.path, args.data_dir)
        elif args.command == 'import':
            cmd_import(args.path, args.data_dir)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
