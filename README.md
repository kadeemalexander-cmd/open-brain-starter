# open-brain-starter

A compiled second brain on Supabase + pgvector. Database is canonical, the wiki regenerates nightly. Any AI client that speaks MCP can read and write to it. ~45 minutes to stand up.

> Architecture inspired by Nate B. Jones, *"Karpathy's Wiki vs. Open Brain. One Fails When You Need It Most."* (2026-04-22), and his [OB1 reference implementation](https://github.com/NateBJones-Projects/OB1).

## What you're getting

```
open-brain-starter/
├── schema.sql                ← run once in your Supabase SQL editor
├── mcp-server/               ← Deno + Hono Supabase Edge Function
│   ├── index.ts              ← four tools: capture, search, list, stats
│   ├── deno.json
│   └── README.md             ← deploy notes
├── compiler/
│   ├── wiki-compile.py       ← reads thoughts, writes one .md per topic
│   ├── requirements.txt
│   └── README.md
├── memory-sync/              ← optional: sync Claude Code memory files
│   ├── sync-memory.py
│   └── README.md
├── vault-skeleton/           ← starting point for your local vault
│   └── CLAUDE.md             ← template; replace the identity block
├── scheduling/               ← cron / launchd / systemd templates
│   ├── crontab.example
│   ├── launchd.plist.template
│   └── systemd.service.template
├── PROMPT.md                 ← paste this into Claude Code; walks through setup
├── docs/                     ← rendered setup-guide HTML, served by GitHub Pages
└── LICENSE                   ← MIT
```

## Live setup guide

Rendered HTML version of the setup guide is published at GitHub Pages — open the **Pages** link in this repo's About sidebar, or visit `docs/index.html` locally.

## Quickstart

If you'd rather have Claude walk you through it, paste [`PROMPT.md`](./PROMPT.md) into a fresh Claude Code session in this directory and follow along. Otherwise:

1. **Create a Supabase project.** Free tier is plenty.
2. **Run [`schema.sql`](./schema.sql)** in the SQL editor (one shot, all six blocks).
3. **Deploy the Edge Function:**
   ```bash
   cd mcp-server
   supabase functions deploy open-brain-mcp
   supabase secrets set \
     OPENROUTER_API_KEY=<sk-or-...> \
     MCP_ACCESS_KEY=$(openssl rand -hex 32)
   ```
4. **Smoke-test capture** — see [`mcp-server/README.md`](./mcp-server/README.md).
5. **Clone the vault skeleton** to where you want your wiki:
   ```bash
   cp -R vault-skeleton ~/open-brain
   cp compiler/wiki-compile.py ~/open-brain/meta/
   ```
6. **Drop your service-role key** into `~/.open-brain-supabase-secret` (`chmod 600`).
7. **Pick your three domains.** Edit `DOMAINS` and `DOMAIN_KEYWORDS` at the top of `wiki-compile.py`.
8. **Wire the MCP server into Claude Code.** Add to `~/.claude.json`:
   ```json
   {
     "mcpServers": {
       "open-brain": {
         "type": "http",
         "url": "https://<your-project>.supabase.co/functions/v1/open-brain-mcp",
         "headers": { "x-brain-key": "<your MCP_ACCESS_KEY>" }
       }
     }
   }
   ```
9. **Wire it into Claude Desktop** — Settings → Connectors → Add custom connector → paste the same URL plus the `x-brain-key` header.
10. **Capture your first thought** through Claude:
    > remember this: kicked off Open Brain today. domains will be `<a>`, `<b>`, `<c>`.
11. **Run the compiler manually once:**
    ```bash
    SUPABASE_URL=https://<your-project>.supabase.co \
      OB_VAULT=$HOME/open-brain \
      python3 ~/open-brain/meta/wiki-compile.py
    ```
12. **Schedule it.** Pick your platform from [`scheduling/`](./scheduling) and follow the comments in the template.

### Optional: sync your Claude Code memory files

Claude Code keeps an auto-memory folder at `~/.claude/projects/<slug>/memory/` with feedback rules, project context, and references it's learned about you. To capture those into Open Brain too, see [`memory-sync/`](./memory-sync). The script is idempotent and can be scheduled with the same cron/launchd/systemd patterns as the compiler.

## Customizing for you

The only opinionated parts:

- **`DOMAINS` and `DOMAIN_KEYWORDS`** at the top of `compiler/wiki-compile.py`. Default is `("work", "side-projects", "personal")` with example keywords. Edit to match how you actually organize your life.
- **`vault-skeleton/CLAUDE.md`** — replace the `Who this is for` block with your own identity. This file becomes the context every AI session loads.
- **The schedule time** in `scheduling/`. 5 AM is the default. Pick whatever doesn't fight with your active hours.

Everything else (the schema, the MCP server, the compiler core) you can leave alone unless you want to extend with your own tools.

## Why this design

A markdown-as-canonical wiki rots — you forget to update it and silent drift kills trust. Open Brain inverts that: capture a thought, it lands in the database with an embedding and metadata, and the wiki recompiles itself nightly. To fix wrong info, you capture a corrective thought; you never edit the markdown.

## License

MIT — fork freely.
