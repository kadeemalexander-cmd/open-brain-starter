# compiler

Reads thoughts from your Supabase project via PostgREST, clusters them by topic, and writes one markdown page per topic to your local vault.

## Install

```bash
pip install -r requirements.txt
```

## Configure

| Var | Default | What |
|---|---|---|
| `SUPABASE_URL` | required | `https://<your-project>.supabase.co` |
| `OB_VAULT` | `~/open-brain` | Where compiled .md pages get written |
| `OB_SECRET_PATH` | `~/.open-brain-supabase-secret` | File containing your service-role key |

## Customize your domains

Open `wiki-compile.py` and edit:

```python
DOMAINS = ("work", "side-projects", "personal")
DEFAULT_DOMAIN = "personal"

DOMAIN_KEYWORDS = {
    "work": ["meeting", "1:1", "standup", "ticket", "deploy", "incident", "oncall"],
    "side-projects": ["side project", "weekend hack", "open source"],
}
```

The compiler routes each thought:

1. By `metadata.folder` (set explicitly when capturing).
2. By keyword match against `metadata.topics` and the first 400 chars of content.
3. Otherwise, into `DEFAULT_DOMAIN`.

## Run

```bash
SUPABASE_URL=https://<your-project>.supabase.co python3 wiki-compile.py
```

## Output

```
<vault>/<domain>/
├── compiled/
│   ├── <topic-slug-1>.md
│   ├── <topic-slug-2>.md
│   └── ...
└── compiled-index.md
```

Plus a run log at `<vault>/meta/dream-logs/YYYY-MM-DD.md`.

Anything in `compiled/` gets wiped and regenerated on the next run. To change what a wiki page says, capture a new thought via any MCP-connected AI; the next compile reflects it.
