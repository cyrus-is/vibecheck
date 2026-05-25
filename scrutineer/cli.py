"""Command-line front door: ``scrutineer install [target]``.

Reachable two ways, both running the same shared core:
    python -m scrutineer install /path/to/repo        # from a clone
    pip install scrutineer && scrutineer install .    # from PyPI
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, installer


def _add_install_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "install",
        help="Install the full Scrutineer skill set into a repo.",
        description=(
            "Copy the servicemap + mcp skills and generate the peer-review and "
            "security-review skills into TARGET/.claude/commands/, all named scrutineer-*."
        ),
    )
    p.add_argument(
        "target", nargs="?", default=".",
        help="Repo to install into (default: current directory).",
    )
    sm = p.add_mutually_exclusive_group()
    sm.add_argument(
        "--crawl", action="store_true",
        help="If no servicemap.json exists, run a headless `claude -p` crawl to create one.",
    )
    sm.add_argument(
        "--service-map", "-s", metavar="PATH", default=None,
        help="Use an existing service map at PATH instead of discovering/crawling.",
    )
    p.add_argument(
        "--force", "-f", action="store_true",
        help="Overwrite existing command files.",
    )
    p.set_defaults(func=_cmd_install)


def _cmd_install(args: argparse.Namespace) -> int:
    try:
        result = installer.install(
            args.target,
            crawl=args.crawl,
            service_map=args.service_map,
            force=args.force,
        )
    except (FileNotFoundError, NotADirectoryError, RuntimeError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    print("\n" + "─" * 60)
    if result.installed:
        print(f"✓ Installed into {result.target}/.claude/commands/:")
        for name in result.installed:
            print(f"    /{name[:-3]}")  # strip .md → slash command name
    else:
        print("Nothing was written (all targets existed; re-run with --force).")
    if result.skipped_crawl:
        print(
            "\nNote: skills were generated without a service map. For cross-service\n"
            "      awareness, run /scrutineer-servicemap in Claude Code, then re-run\n"
            "      `scrutineer install --force` (or pass --crawl)."
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrutineer",
        description="Agentic code review toolkit — installer.",
    )
    parser.add_argument("--version", action="version", version=f"scrutineer {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_install_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
