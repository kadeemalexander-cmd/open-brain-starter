#!/usr/bin/env python3
"""
sync-memory.py — Sync Claude Code's local memory files into Open Brain.

Claude Code writes auto-memory files (feedback rules, project context,
references) to ~/.claude/projects/<project-slug>/memory/. This script walks
every project's memory/ folder, reads each .md file, and captures it as a
thought via your Open Brain MCP endpoint.

Idempotent — re-runs are safe. The schema's `upsert_thought` function dedupes
by SHA-256 fingerprint of normalized content.

Usage:

    MCP_URL=https://<your-project>.supabase.co/functions/v1/open-brain-mcp \\
    MCP_ACCESS_KEY=<your-key> \\
    python3 sync-memory.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
MCP_URL = os.environ.get("MCP_URL")
MCP_ACCESS_KEY = os.environ.get("MCP_ACCESS_KEY")
MEMORY_ROOT = Path(os.environ.get(
    "OB_MEMORY_ROOT",
    "~/.claude/projects",
)).expanduser()
SLEEP_BETWEEN = float(os.environ.get("OB_SYNC_SLEEP", "0.4"))

if not MCP_URL or not MCP_ACCESS_KEY:
    print("ERROR: set MCP_URL and MCP_ACCESS_KEY env vars", file=sys.stderr)
    sys.exit(1)


def find_memory_files() -> list[Path]:
    """All Claude Code memory files across every project on this machine."""
    if not MEMORY_ROOT.exists():
        return []
    files: list[Path] = []
    for memory_dir in MEMORY_ROOT.glob("*/memory"):
        for md in memory_dir.glob("*.md"):
            # Skip the index — it's just a list of pointers, not a memory.
            if md.name == "MEMORY.md":
                continue
            files.append(md)
    return sorted(files)


def capture(content: str) -> tuple[bool, str]:
    """POST one thought to the MCP. Returns (ok, message)."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "capture_thought",
            "arguments": {"content": content},
        },
    }
    req = urllib.request.Request(
        MCP_URL,
        method="POST",
        headers={
            "x-brain-key": MCP_ACCESS_KEY,
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="replace")
            return (200 <= r.status < 300, body[:300])
    except urllib.error.HTTPError as e:
        return (False, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}")
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}")


def main() -> int:
    files = find_memory_files()
    if not files:
        print(f"no memory files found under {MEMORY_ROOT}")
        return 0

    print(f"Found {len(files)} memory files under {MEMORY_ROOT}")
    synced, failed = 0, 0
    for f in files:
        body = f.read_text(encoding="utf-8", errors="replace").strip()
        if not body:
            continue

        # Prepend the filename so the LLM has stable context for metadata
        # extraction. Memory files already have rich frontmatter (name, type,
        # description) which the extractor will pick up as topics/type.
        content = f"# {f.stem}\n\n{body}"

        ok, msg = capture(content)
        if ok:
            synced += 1
            print(f"  OK  {f.name}")
        else:
            failed += 1
            print(f"  FAIL {f.name}  {msg}")

        time.sleep(SLEEP_BETWEEN)

    print(f"\nDone. Synced: {synced}  Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
