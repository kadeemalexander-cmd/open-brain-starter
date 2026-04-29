#!/usr/bin/env python3
"""
wiki-compile.py — Open Brain wiki compiler

Reads from your Open Brain (Supabase + pgvector) and regenerates a readable
markdown wiki under <vault>/<domain>/compiled/.

Architecture:
  - Open Brain DB = source of truth
  - Vault wiki = compiled view, regenerated on each run
  - To fix a wiki page, capture a corrective thought; the next run picks it up.
  - Never edit compiled pages by hand.

Run:  python3 wiki-compile.py
Cron: 0 5 * * *  cd ~/open-brain && /usr/bin/python3 meta/wiki-compile.py
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests

# ── Config (read from env, fall back to sensible defaults) ───────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SECRET_KEY_PATH = Path(os.environ.get("OB_SECRET_PATH", "~/.open-brain-supabase-secret")).expanduser()
VAULT = Path(os.environ.get("OB_VAULT", "~/open-brain")).expanduser()
TODAY = datetime.now().strftime("%Y-%m-%d")

if not SUPABASE_URL:
    print("ERROR: set SUPABASE_URL env var (e.g. https://<your-project>.supabase.co)", file=sys.stderr)
    sys.exit(1)
if not SECRET_KEY_PATH.exists():
    print(f"ERROR: missing service-role key at {SECRET_KEY_PATH}", file=sys.stderr)
    print("       create it with `chmod 600` and paste your Supabase service-role key", file=sys.stderr)
    sys.exit(1)

SECRET_KEY = SECRET_KEY_PATH.read_text().strip()

HEADERS = {
    "apikey": SECRET_KEY,
    "Authorization": f"Bearer {SECRET_KEY}",
    "Content-Type": "application/json",
}

# ── Domain config ────────────────────────────────────────────────────────────
# Customize this for your three domains. The compiler routes each thought to
# a domain by:
#   1. metadata.folder match (set explicitly when capturing)
#   2. keyword match against topics + first 400 chars of content
#   3. fall back to DEFAULT_DOMAIN below.
DOMAINS = ("work", "side-projects", "personal")
DEFAULT_DOMAIN = "personal"

DOMAIN_KEYWORDS = {
    "work": ["meeting", "1:1", "standup", "ticket", "deploy", "incident", "oncall"],
    "side-projects": ["side project", "weekend hack", "open source"],
    # add your own keywords. anything not matched lands in DEFAULT_DOMAIN.
}


# ── Domain routing ───────────────────────────────────────────────────────────
def domain_for(thought: dict) -> str:
    md = thought.get("metadata") or {}
    folder = (md.get("folder") or "").lower()
    for d in DOMAINS:
        if d in folder:
            return d

    haystack = (
        " ".join(md.get("topics") or [])
        + " "
        + (thought.get("content", "")[:400] or "")
    ).lower()
    for dom, kws in DOMAIN_KEYWORDS.items():
        if any(k in haystack for k in kws):
            return dom
    return DEFAULT_DOMAIN


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower())
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:60] or "untitled"


def topic_for(thought: dict) -> str:
    md = thought.get("metadata") or {}
    topics = md.get("topics") or []
    if topics:
        return topics[0]
    title = md.get("title") or thought.get("content", "").splitlines()[0][:60]
    return title or "untitled"


# ── Fetch ────────────────────────────────────────────────────────────────────
def fetch_all() -> list:
    out, offset, page = [], 0, 1000
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/thoughts?select=id,content,metadata,created_at"
            f"&order=created_at.desc&limit={page}&offset={offset}"
        )
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        chunk = r.json()
        out.extend(chunk)
        if len(chunk) < page:
            break
        offset += page
    return out


# ── Compile ──────────────────────────────────────────────────────────────────
def compile_topic_page(domain: str, topic: str, thoughts: list) -> str:
    lines = [
        "---",
        f"title: {topic}",
        f"domain: {domain}",
        f"compiled_at: {datetime.now().isoformat(timespec='seconds')}",
        "source: open-brain-db",
        f"thought_count: {len(thoughts)}",
        "warning: GENERATED FILE — do not edit. Edit the underlying thoughts in Open Brain.",
        "---",
        "",
        f"# {topic}",
        "",
        f"_{len(thoughts)} thoughts compiled from Open Brain on {TODAY}._",
        "",
    ]
    for t in sorted(thoughts, key=lambda x: x.get("created_at", ""), reverse=True):
        md = t.get("metadata") or {}
        ts = t.get("created_at", "")[:10]
        ttype = md.get("type", "note")
        topics = ", ".join((md.get("topics") or [])[:5])
        people = ", ".join(md.get("people") or [])
        actions = md.get("action_items") or []
        src = md.get("source") or "mcp"
        title = md.get("title")

        header_bits = [f"**{ttype}**"]
        if title:
            header_bits.append(f"_{title}_")
        header_bits.append(f"`{ts}`")
        header_bits.append(f"`source: {src}`")
        lines.append("## " + " — ".join(header_bits))
        if topics:
            lines.append(f"*topics: {topics}*")
        if people:
            lines.append(f"*people: {people}*")
        lines.append("")
        lines.append(t["content"].strip())
        if actions:
            lines.append("")
            lines.append("**action items:**")
            for a in actions:
                lines.append(f"- {a}")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def compile_index(domain: str, topics: dict) -> str:
    lines = [
        "---",
        f"title: {domain.upper()} index",
        f"compiled_at: {datetime.now().isoformat(timespec='seconds')}",
        "source: open-brain-db",
        "warning: GENERATED FILE — do not edit.",
        "---",
        "",
        f"# {domain.upper()} — Compiled Wiki Index",
        "",
        f"_{sum(len(v) for v in topics.values())} thoughts across {len(topics)} topics, compiled {TODAY}._",
        "",
        "## Topics",
        "",
    ]
    for topic in sorted(topics, key=lambda t: -len(topics[t])):
        slug = slugify(topic)
        lines.append(f"- [{topic}](compiled/{slug}.md) — {len(topics[topic])} thoughts")
    return "\n".join(lines)


# ── Run ──────────────────────────────────────────────────────────────────────
def main():
    print(f"[{TODAY}] Fetching thoughts from Open Brain at {SUPABASE_URL}...")
    thoughts = fetch_all()
    print(f"  {len(thoughts)} thoughts fetched")

    by_domain_topic: dict = defaultdict(lambda: defaultdict(list))
    for t in thoughts:
        d = domain_for(t)
        topic = topic_for(t)
        by_domain_topic[d][topic].append(t)

    for domain in DOMAINS:
        topics = by_domain_topic.get(domain, {})
        compiled_dir = VAULT / domain / "compiled"
        compiled_dir.mkdir(parents=True, exist_ok=True)
        # Wipe stale compiled pages, but only the auto-generated dir
        for old in compiled_dir.glob("*.md"):
            old.unlink()

        if not topics:
            print(f"  [{domain}] no thoughts")
            continue

        for topic, ts in topics.items():
            page = compile_topic_page(domain, topic, ts)
            slug = slugify(topic)
            (compiled_dir / f"{slug}.md").write_text(page)

        idx = compile_index(domain, topics)
        (VAULT / domain / "compiled-index.md").write_text(idx)
        print(f"  [{domain}] {sum(len(v) for v in topics.values())} thoughts → {len(topics)} topic pages")

    # Dream log
    log_path = VAULT / "meta" / "dream-logs" / f"{TODAY}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = [
        f"# Wiki Compile — {TODAY}",
        "",
        "_Architecture: hybrid (Open Brain DB = source of truth, vault = generated view)._",
        "",
        "## Run summary",
        "",
        f"- thoughts fetched: {len(thoughts)}",
    ]
    for d in DOMAINS:
        topics = by_domain_topic.get(d, {})
        total = sum(len(v) for v in topics.values())
        log.append(f"- {d}: {total} thoughts → {len(topics)} compiled topic pages")
    log.append("")
    log.append("## Notes")
    log.append("")
    log.append("- Compiled wiki pages live under `<domain>/compiled/` — never edit by hand.")
    log.append("- To change a wiki page: capture the new thought via any MCP-connected AI; next run regenerates.")
    log_path.write_text("\n".join(log))
    print(f"[done] log: {log_path}")


if __name__ == "__main__":
    main()
