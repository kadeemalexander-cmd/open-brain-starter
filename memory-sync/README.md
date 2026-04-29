# memory-sync

Optional. Sync Claude Code's local memory files into your Open Brain.

## Why

Claude Code writes auto-memory files to `~/.claude/projects/<project-slug>/memory/`. They look like this:

```
~/.claude/projects/<slug>/memory/
├── MEMORY.md                                ← index (skipped by this syncer)
├── feedback_no_meetings_after_5pm.md
├── feedback_terse_responses.md
├── project_<your-thing>.md
├── reference_<oncall|docs|wiki>.md
└── user_role.md
```

Each is a standalone markdown memory with frontmatter. They live on your laptop only — if you reinstall Claude Code, switch machines, or move to a different AI client, they don't follow you.

This syncer pushes them into Open Brain so they:

- Survive machine moves
- Become semantically searchable alongside everything else
- Show up in your nightly compiled wiki under whichever domain matches them

It's idempotent — re-runs don't create duplicates because the schema's `upsert_thought` function dedupes by SHA-256 fingerprint.

## Setup

1. Make sure your MCP server is deployed and reachable (you already did this from the top-level README).
2. Set the two env vars:

   ```bash
   export MCP_URL="https://<your-project>.supabase.co/functions/v1/open-brain-mcp"
   export MCP_ACCESS_KEY="<the same key you set in the Edge Function secrets>"
   ```

3. Smoke-test once manually:

   ```bash
   python3 sync-memory.py
   ```

   You should see one line per memory file ending with `Synced: N  Failed: 0`. The first run captures everything; subsequent runs are no-ops on unchanged files.

4. Verify in Supabase Studio:

   ```sql
   select content, metadata, created_at
   from thoughts
   where metadata->>'source' = 'mcp'
   order by created_at desc
   limit 10;
   ```

## Schedule

Run it before your nightly wiki compile so the memory thoughts land in the next compiled view.

### cron

```cron
# 4 AM, an hour before the wiki compile
0 4 * * *  MCP_URL="https://<your-project>.supabase.co/functions/v1/open-brain-mcp" \
           MCP_ACCESS_KEY="<your-key>" \
           /usr/bin/python3 $HOME/open-brain/memory-sync/sync-memory.py \
           >> $HOME/open-brain/meta/dream-logs/memory-sync.log 2>&1
```

### launchd / systemd

Same pattern as the compiler — copy the templates from `../scheduling/`, change `ExecStart` to point at this script, change the time to 4 AM, add `MCP_URL` and `MCP_ACCESS_KEY` to the environment.

## Customize

| Env var | Default | What |
|---|---|---|
| `MCP_URL` | required | Your Edge Function URL |
| `MCP_ACCESS_KEY` | required | Your `MCP_ACCESS_KEY` |
| `OB_MEMORY_ROOT` | `~/.claude/projects` | Where Claude Code keeps project memory folders |
| `OB_SYNC_SLEEP` | `0.4` | Seconds between calls. Bump if you hit OpenRouter rate limits. |

## What this does NOT do

- It does **not** delete thoughts when you delete a memory file. Captures are append-only by design.
- It does **not** sync `MEMORY.md` — that's an index, not a memory itself.
- It does **not** look outside `~/.claude/projects/`. For other note tools (Obsidian vault, Apple Notes), use OB1 import recipes — they're separate.
