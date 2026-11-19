"""Summarize Claude Code session history: duration, turns and token usage per session.

Claude Code saves each session as a .jsonl file. The agent container mounts the
host folder ../agent-history at /root/.claude/projects so those files survive
after the container exits. This script reads them and prints one row per session.

Usage (from the repository root):
    python agent/tools/session_report.py                # default: ../agent-history
    python agent/tools/session_report.py PATH           # another history folder
    python agent/tools/session_report.py --csv          # CSV output for spreadsheets

Uses only the Python standard library.
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_time(value):
    """Parse an ISO timestamp such as 2026-11-19T02:29:35.747Z."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def summarize(path):
    """Return a summary dict for one session file."""
    usage_by_id = {}
    main_turns = set()
    user_prompts = 0
    times = []
    models = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            stamp = parse_time(entry.get("timestamp"))
            if stamp:
                times.append(stamp)
            message = entry.get("message") or {}
            if entry.get("type") == "user" and not entry.get("isSidechain"):
                content = message.get("content")
                tool_only = isinstance(content, list) and content and all(
                    isinstance(block, dict) and block.get("type") == "tool_result" for block in content
                )
                if not tool_only:
                    user_prompts += 1
            if message.get("model"):
                models.add(message["model"])
            usage = message.get("usage")
            if usage and message.get("id"):
                # Streamed messages repeat the same id with the same usage; count each once.
                usage_by_id[message["id"]] = usage
                if entry.get("type") == "assistant" and not entry.get("isSidechain"):
                    main_turns.add(message["id"])
    tokens_in = sum(
        u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        for u in usage_by_id.values()
    )
    tokens_out = sum(u.get("output_tokens", 0) for u in usage_by_id.values())
    start, end = (min(times), max(times)) if times else (None, None)
    return {
        "session": path.stem[:8],
        "project": path.parent.name,
        "start_utc": start.strftime("%Y-%m-%d %H:%M") if start else "",
        "minutes": round((end - start).total_seconds() / 60, 1) if start else 0,
        "prompts": user_prompts,
        "api_calls": len(main_turns),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "models": ",".join(sorted(m for m in models if not m.startswith("<"))),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", nargs="?", default=str(Path("..") / "agent-history"))
    parser.add_argument("--csv", action="store_true", help="print CSV instead of a table")
    args = parser.parse_args()

    files = sorted(Path(args.folder).glob("*/*.jsonl"))
    if not files:
        print(f"No session files found under {args.folder}", file=sys.stderr)
        return 1
    rows = sorted((summarize(f) for f in files), key=lambda r: r["start_utc"])

    if args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return 0

    headers = list(rows[0])
    widths = {h: max(len(h), *(len(str(r[h])) for r in rows)) for h in headers}
    print("  ".join(h.ljust(widths[h]) for h in headers))
    for row in rows:
        print("  ".join(str(row[h]).ljust(widths[h]) for h in headers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
