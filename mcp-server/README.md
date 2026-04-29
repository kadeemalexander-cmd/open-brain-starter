# mcp-server — Open Brain Edge Function

A Supabase Edge Function (Deno + Hono) that exposes four MCP tools:

| Tool | What it does |
|---|---|
| `capture_thought` | Save a thought — generates a 1536-dim embedding, auto-extracts metadata (topics, people, action_items, type), upserts on content fingerprint. |
| `search_thoughts` | Semantic search — embedding similarity against the `thoughts` table. |
| `list_thoughts` | List recent thoughts with optional filters (type, topic, person, days). |
| `thought_stats` | Counts by type, top topics, top people. |

## Required env vars

| Variable | Source |
|---|---|
| `SUPABASE_URL` | Auto-populated by Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Auto-populated by Supabase |
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) — for embeddings + metadata extraction. Free tier available. |
| `MCP_ACCESS_KEY` | Generate with `openssl rand -hex 32`. Required on every HTTP call as the `x-brain-key` header. |

Set them with:

```bash
supabase secrets set \
  OPENROUTER_API_KEY=sk-or-... \
  MCP_ACCESS_KEY=$(openssl rand -hex 32)
```

(`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are injected automatically by Supabase on every Edge Function — you don't need to set them.)

## Deploy

```bash
# from this directory
supabase login                                # one-time
supabase link --project-ref <your-ref>        # one-time per machine
supabase functions deploy open-brain-mcp
```

Function URL:

```
https://<your-project>.supabase.co/functions/v1/open-brain-mcp
```

## Smoke test

```bash
curl -X POST "https://<your-project>.supabase.co/functions/v1/open-brain-mcp" \
  -H "x-brain-key: <your MCP_ACCESS_KEY>" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"capture_thought","arguments":{"content":"hello brain"}}}'
```

Expect a JSON-RPC response with the new thought ID.

## Auth

Every request must include either:

- header `x-brain-key: <MCP_ACCESS_KEY>`, OR
- query string `?key=<MCP_ACCESS_KEY>` (useful when registering with clients that don't let you set custom headers easily).

Requests without a valid key get a `401`.

## Local development

```bash
supabase functions serve open-brain-mcp --env-file .env.local
```

Where `.env.local` contains all four env vars above.

## Why OpenRouter

OpenRouter proxies many model vendors behind a single API:

- One key works for both the embedding model (`openai/text-embedding-3-small`) and the metadata-extraction model (`openai/gpt-4o-mini`).
- Easy to swap models without touching code — change the model string in `index.ts`.
- A free tier covers casual usage.

If you'd rather run embeddings locally (Ollama) and skip the third-party dependency, swap `getEmbedding()` to call your local Ollama endpoint and `extractMetadata()` to call a local chat model. The function won't care — it just needs back a 1536-dim vector and a JSON object.

## Notes

- The CORS preflight at the top of `index.ts` is required for browser/Electron clients (Claude Desktop, claude.ai web).
- The `Accept: text/event-stream` patch is a workaround for Claude Desktop, which doesn't send that header by default but the streamable HTTP transport requires it.
