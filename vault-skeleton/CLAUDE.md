# Vault README

> This vault is a **compiled view** of your Open Brain database. The DB at
> Supabase is canonical. Pages under `<domain>/compiled/` are regenerated
> nightly by `meta/wiki-compile.py`. Do not hand-edit them.

## Who this is for

Replace this section with your own identity block when you fork. A useful
identity block includes:

- Name and current role
- 2–3 sentences on what kinds of thoughts you'll be capturing
- The three domains you've chosen (and why)

This is the file every AI session loads when working with your vault, so
write it in the second person ("you are working with X who…").

## Layout

```
your-vault/
├── CLAUDE.md                          ← this file (your identity + rules)
├── meta/
│   ├── wiki-compile.py                ← the compiler (symlink or copy)
│   └── dream-logs/YYYY-MM-DD.md       ← compile run logs
│
├── <domain-1>/                        ← pick your three domains
│   ├── compiled/                      ← GENERATED. one .md per topic.
│   └── compiled-index.md              ← GENERATED domain index.
│
├── <domain-2>/   (same shape)
└── <domain-3>/   (same shape)
```

## How knowledge enters

**Direct capture** — say "remember this:" or "save this to my brain:" to any
MCP-connected AI. The AI calls `capture_thought`. The Edge Function generates
an embedding and auto-extracts metadata (topics, people, action items, type).

## How the wiki gets compiled

`python3 meta/wiki-compile.py` does the work. Schedule it nightly with cron,
launchd, or systemd (templates in the starter's `scheduling/` directory).

Output: under each `<domain>/compiled/`, one `<topic>.md` per topic cluster,
plus `<domain>/compiled-index.md`.

## Rules

1. **Open Brain DB is canonical.** This vault is downstream.
2. **Never edit `<domain>/compiled/`.** It's regenerated. Edits get overwritten.
3. **To fix wrong info:** capture a corrected thought via any AI, then re-run
   the compiler. Don't patch markdown.
4. **Sensitive personal context** stays in your `personal` (or equivalent)
   domain. The router uses metadata folder + topic keywords + content head to
   assign domains.

## Authority hierarchy

1. Open Brain `thoughts` table — canonical
2. ADRs in tracked codebases — canonical for that code
3. This file (`CLAUDE.md`) — your schema/rules
4. Compiled wiki pages — derived, never canonical
