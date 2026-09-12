#!/usr/bin/env python3
"""
install_skill.py - install the bundled `sequential-thinking` skill into a project.

The skill under `skills/sequential-thinking/` is written with BARE tool names
(`process_thought`, `generate_summary`, ...) because that is what this server registers.
Hosts, however, expose MCP tools under a prefix of their own: Claude Code as
`mcp__<server>__<tool>`, OpenCode as `<server>_<tool>`. Leaving that conversion to the
model is how a skill ends up naming tools that do not exist, so it happens HERE, once, at
install time - the installed copy names the tools exactly as its host does.

Nothing else is touched: wiring the MCP server itself into the host's config is a separate
step the README covers.

Usage:
    python install_skill.py --target ../my-project
    python install_skill.py --target ../my-project --runner opencode
    python install_skill.py --runner claude-user
    python install_skill.py --target ../my-project --dry-run
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SKILL_NAME = "sequential-thinking"
SOURCE_DIR = Path(__file__).resolve().parent / "skills" / SKILL_NAME

# The tools this server registers (mcp_sequential_thinking/server.py). Keep in sync with it:
# a name listed here that the server does not expose would be rewritten into a tool that
# does not exist, which is the exact failure this script is meant to prevent.
TOOL_NAMES = (
    "process_thought",
    "generate_summary",
    "clear_history",
    "export_session",
    "import_session",
    "list_sessions",
)

# runner -> (destination relative to target, prefix template, is_user_level)
RUNNERS = {
    "claude": (Path(".claude") / "skills" / SKILL_NAME, "mcp__{server}__", False),
    "claude-user": (Path(".claude") / "skills" / SKILL_NAME, "mcp__{server}__", True),
    "opencode": (Path(".opencode") / "skills" / SKILL_NAME, "{server}_", False),
    "raw": (Path("skills") / SKILL_NAME, "", False),
}

# A bare tool name is one not already carrying a prefix: no word character, `_` or `-`
# immediately before it. That lookbehind is what makes a second run a no-op instead of
# producing `mcp__x__mcp__x__process_thought`.
TOOL_RE = re.compile(r"(?<![\w-])(" + "|".join(TOOL_NAMES) + r")\b")


def rewrite(text: str, prefix: str) -> str:
    """Prefix every bare tool name in `text`. No-op when `prefix` is empty."""
    if not prefix:
        return text
    return TOOL_RE.sub(lambda m: prefix + m.group(1), text)


def resolve_dest(args: argparse.Namespace) -> Path:
    rel, _, user_level = RUNNERS[args.runner]
    if args.dest:
        return Path(args.dest).expanduser().resolve()
    if user_level:
        return (Path.home() / rel).resolve()
    if not args.target:
        raise SystemExit(
            "error: --target is required for --runner %s (or pass --dest)" % args.runner
        )
    return (Path(args.target).expanduser().resolve() / rel).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the sequential-thinking skill into a project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[-1],
    )
    parser.add_argument("--target", help="root directory of the destination project")
    parser.add_argument(
        "--runner",
        choices=sorted(RUNNERS),
        default="claude",
        help="host to install for: decides both the destination path and the tool-name "
        "prefix (default: claude)",
    )
    parser.add_argument(
        "--server-name",
        default=SKILL_NAME,
        help="MCP server name as registered in the host's config; the prefix is built "
        "from it (default: %(default)s)",
    )
    parser.add_argument("--dest", help="write here, ignoring the --runner path rule")
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing destination"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print what would be written, then stop"
    )
    args = parser.parse_args(argv)

    if not SOURCE_DIR.is_dir():
        raise SystemExit("error: skill source not found at %s" % SOURCE_DIR)

    prefix = RUNNERS[args.runner][1].format(server=args.server_name)
    dest = resolve_dest(args)
    sources = sorted(p for p in SOURCE_DIR.rglob("*") if p.is_file())

    print("source:  %s" % SOURCE_DIR)
    print("dest:    %s" % dest)
    print("runner:  %s" % args.runner)
    print("tools:   %s" % (prefix + TOOL_NAMES[0] if prefix else TOOL_NAMES[0]))
    for src in sources:
        print("  %s" % (dest / src.relative_to(SOURCE_DIR)))

    if args.dry_run:
        print("\ndry run: nothing written")
        return 0

    if dest.exists():
        if not args.force:
            raise SystemExit(
                "error: %s already exists; pass --force to overwrite it" % dest
            )
        shutil.rmtree(dest)

    for src in sources:
        out = dest / src.relative_to(SOURCE_DIR)
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() == ".md":
            # newline="" on both sides: read and write the file's own line endings
            # instead of translating them to the platform's, so an installed copy
            # differs from the source only in the tool names. (open() rather than
            # Path.read_text, which only grew a newline argument in 3.13.)
            with src.open("r", encoding="utf-8", newline="") as fh:
                text = fh.read()
            with out.open("w", encoding="utf-8", newline="") as fh:
                fh.write(rewrite(text, prefix))
        else:
            shutil.copy2(src, out)

    print("\ninstalled %d file(s)." % len(sources))
    if prefix:
        print(
            "Tools are named %s* in this copy - check that against the tool list your "
            "host shows for the MCP server you registered as '%s'."
            % (prefix, args.server_name)
        )
    else:
        print("Tool names left bare - the host must expose them unprefixed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
