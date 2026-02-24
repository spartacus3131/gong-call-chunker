# Gong Call Chunker - AI Context

## What This Project Does

Extracts structured intelligence from sales call transcripts using Claude AI. Customers define what to extract in YAML configs (fields like restaurant_size, pain_points, competitors), and the chunker dynamically builds Claude tool-use prompts at runtime. No code changes needed to add new extraction fields.

## Architecture

```
config/customers/*.yaml     ← Customer extraction schemas (THE customization point)
config/default.yaml         ← Base fields inherited by all customers
        ↓
src/call_chunker.py         ← Builds Claude tool-use schema from YAML, extracts structured data
src/schema_loader.py        ← Loads/merges YAML configs, converts to prompt instructions
src/transcript_parser.py    ← Normalizes Gong JSON / raw text / CSV to common format
src/gong_client.py          ← Gong API integration (auth, list calls, fetch transcripts)
        ↓
api/main.py                 ← FastAPI app with auth middleware
api/models.py               ← SQLAlchemy models: Customer, Call, CallChunk, CallField, CallSummary
api/routers/calls.py        ← CRUD, upload, chunk, Gong sync
api/routers/chunks.py       ← Search across calls by text + field filters
api/routers/schemas.py      ← CRUD for customer YAML schemas (with path traversal protection)
api/routers/analytics.py    ← Aggregate analytics (pain points, competitors, deal likelihood)
api/auth.py                 ← X-API-Key auth (disabled when API_KEYS env not set)
        ↓
web/src/app/                ← Next.js 14 frontend
web/src/app/page.tsx        ← Dashboard
web/src/app/calls/          ← Call library + call detail (chunks, fields, transcript tabs)
web/src/app/schemas/        ← Schema editor (visual + raw JSON)
web/src/app/analytics/      ← Analytics dashboard with bar charts
web/src/lib/api.ts          ← API client + TypeScript types
```

## Key Design Decisions

- **Claude tool use for structured output** — `call_chunker.py` builds a JSON Schema tool definition dynamically from the customer YAML. Claude is forced to return valid structured data matching the schema. No fragile JSON string parsing.
- **JSONB for chunk content** — CallChunk.content is JSONB so different customers can have different chunk structures without schema changes.
- **EAV pattern for CallField** — Extracted fields stored as rows (field_name, field_value) so they're queryable via SQL regardless of which customer schema produced them.
- **YAML over JSON for configs** — More readable, supports comments, easier for non-technical users to edit.
- **Merge-based schema inheritance** — Customer configs merge on top of `default.yaml`. Customer fields override defaults with the same name; default-only fields are appended.

## Running Locally

```bash
# Database
docker compose up db -d

# API (Terminal 1)
pip install -r requirements.txt
alembic upgrade head
uvicorn api.main:app --reload --port 8000

# Frontend (Terminal 2)
cd web && npm install && npm run dev
```

API docs: http://localhost:8000/docs
Web UI: http://localhost:3000

## Environment Variables

- `ANTHROPIC_API_KEY` — Required for chunking
- `DATABASE_URL` — PostgreSQL connection (default: postgresql://gong:gong@localhost:5432/gong_chunker)
- `API_KEYS` — Comma-separated API keys (if unset, auth disabled for dev)
- `GONG_API_KEY` / `GONG_API_SECRET` — Optional, for Gong API sync
- `CLAUDE_MODEL` — Default: claude-sonnet-4-20250514

## Working Instructions

### When adding a new customer config
1. Create `config/customers/{slug}.yaml` following the touchbistro.yaml pattern
2. The schema_loader auto-discovers YAML files in that directory
3. No code changes or migrations needed — JSONB + EAV handle any field structure
4. Test with: `python -c "from src.schema_loader import load_customer_schema; print(load_customer_schema('your_slug'))"`

### When modifying the chunker
- The extraction tool schema is built in `CallChunker._build_extraction_tool()`
- Field type mapping is in `CallChunker._field_to_json_schema()`
- If you add a new YAML field type, add a case to `_field_to_json_schema()`
- The system prompt is in `_build_system_prompt()` — keep it concise, the tool schema does the heavy lifting

### When modifying the API
- Use relative imports in `api/` (e.g., `from ..database import get_db`)
- All `/api/v1/*` routes require API key when `API_KEYS` env is set
- Call status lifecycle: `pending` → `processing` → `chunked` (or `failed`)
- Slug validation (`^[a-z0-9][a-z0-9_-]*$`) is enforced on schema endpoints

### When modifying the frontend
- API client and types are in `web/src/lib/api.ts`
- All pages are client components (`"use client"`) using `useState`/`useEffect`
- API calls go through the Next.js rewrite proxy (see `next.config.js`)

## Testing

```bash
python -m pytest tests/ -v
```

Tests cover: schema loading, schema merging, transcript parsing (all formats), tool schema generation, field type mapping. Tests do NOT require an API key or database.

## Common Pitfalls

1. **Don't hardcode extraction fields in Python** — they come from YAML configs at runtime
2. **Don't use `json.loads()` for Claude output** — we use tool use for guaranteed structured responses
3. **Validate slugs** — any endpoint accepting a customer slug must validate it (alphanumeric + hyphens/underscores only) to prevent path traversal
4. **Gong API rate limits** — 3 requests/sec max. The sync endpoint includes `asyncio.sleep(0.35)` between calls
5. **Call status matters** — always set status to `processing` before chunking, `chunked` on success, `failed` on error
