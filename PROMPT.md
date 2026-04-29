# PROMPT — paste into Claude Code

Open a fresh Claude Code session in this directory, then paste the block below as your first message. Claude will read the kit and walk you through setup interactively, pausing whenever it needs your hands (creating the Supabase project, generating secrets, pasting URLs).

```
I want to set up my own Open Brain — a compiled second brain where the
database is canonical and the wiki regenerates nightly. The full kit is in
this directory: schema.sql, mcp-server/, compiler/, memory-sync/,
vault-skeleton/, and scheduling/. Read the top-level README.md first.

Then walk me through the Quickstart steps interactively, in order.
For each step:

1. Tell me what you're about to do and why.
2. If the step needs my hands (creating the Supabase project, generating
   secrets, pasting URLs), pause and tell me exactly what to click or paste.
   Don't fabricate values.
3. If the step is something you can do (deploying the Edge Function with
   the existing source, copying the vault skeleton, customizing the
   DOMAINS tuple in wiki-compile.py, writing my crontab/launchd/systemd
   entry), do it and show me the diff.
4. After each step, run the smoke test if there is one — the curl in
   step 4, the SELECT in step 10, the manual compiler run in step 11 —
   and read the output to me before moving on.

Constraints:
- Use my own Supabase project, not anyone else's.
- Pick three domains with me before customizing wiki-compile.py.
  Mine will be: ___, ___, ___ (ask me).
- chmod 600 on ~/.open-brain-supabase-secret. Don't echo the key back to
  me after I paste.
- Don't move on if a smoke test fails. Stop and debug.

Ready when you are. Read README.md first, then tell me what you'd like
me to do for step 1.
```

## Notes

- The blanks `___, ___, ___` are deliberate — fill them in before pasting, or leave them and Claude will ask. Your three domains can be anything.
- This prompt does NOT auto-run paid signups or destructive operations. Claude pauses on Supabase project creation, secret generation, and Edge Function deployment so you can see what's happening.
- If you'd rather follow the README and run the commands yourself, ignore this file.
