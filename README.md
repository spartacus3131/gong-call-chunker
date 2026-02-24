# Gong Call Chunker

Extract structured intelligence from sales call transcripts using AI-powered chunking. Define what matters to your business in a simple YAML config, and the system extracts it from every call.

## How It Works

```
Call Transcript → Customer YAML Config → Claude AI Extraction → Structured Data in PostgreSQL
```

1. **Upload or sync** call transcripts (paste, file upload, or Gong API)
2. **Define your schema** in a YAML config — what fields to extract (restaurant size, pain points, competitors, etc.)
3. **Chunk the call** — Claude reads the transcript and extracts structured data matching your schema
4. **Query and analyze** — search across calls, filter by any field, view aggregate analytics

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url> && cd gong-call-chunker
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

### 2. Start services

```bash
docker compose up -d    # Starts Postgres, API, and Web
```

Or run locally:

```bash
# Terminal 1: Database
docker compose up db

# Terminal 2: API
pip install -r requirements.txt
alembic upgrade head
uvicorn api.main:app --reload --port 8000

# Terminal 3: Web
cd web && npm install && npm run dev
```

### 3. Seed sample data

```bash
python scripts/seed_sample.py
```

### 4. Open the app

- **Web UI:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

## Adding a New Customer

The key customization point is the YAML config. Create a new file in `config/customers/`:

```yaml
# config/customers/your-company.yaml
customer: your_company
display_name: "Your Company"
industry: your_industry

extraction_schema:
  fields:
    - name: company_size
      type: enum
      options: [startup, smb, mid_market, enterprise]
      description: "Size of the prospect's company"

    - name: pain_points
      type: list
      description: "Specific pain points mentioned"
      examples: [slow_onboarding, manual_processes, poor_reporting]

    - name: current_solution
      type: text
      description: "What they're currently using"

    # Add as many fields as you need...

  chunk_levels:
    - level: topics
      description: "Major discussion topics (5-8 per call)"
      extract: [title, timestamp_start, timestamp_end, summary, relevance_to_sale]

    - level: insights
      description: "Specific customer insights (2-3 per topic)"
      extract: [parent_topic, insight, sentiment, action_item]

    - level: quotes
      description: "Notable verbatim quotes (5-10 per call)"
      extract: [quote, speaker, context, sentiment, tags]

  call_summary:
    - overall_sentiment
    - deal_likelihood
    - next_steps
    - follow_up_date
```

That's it. No code changes needed. The chunker reads your YAML at runtime and builds the Claude extraction prompt dynamically.

## Field Types

| Type | Description | Example |
|------|-------------|---------|
| `enum` | Single value from options list | `restaurant_type: fine_dining` |
| `text` | Free-form text | `current_pos: "Square POS"` |
| `integer` | Number | `location_count: 3` |
| `boolean` | Yes/No | `budget_mentioned: true` |
| `list` | Multiple values | `pain_points: ["scheduling", "reporting"]` |

## Gong API Integration

To sync calls directly from Gong:

1. Get your API credentials from Gong Settings > API
2. Add to `.env`:
   ```
   GONG_API_KEY=your-key
   GONG_API_SECRET=your-secret
   ```
3. Sync via CLI:
   ```bash
   python scripts/sync_gong.py --customer touchbistro --from 2026-01-01
   ```
4. Or via API:
   ```bash
   curl -X POST http://localhost:8000/api/v1/calls/sync/gong \
     -H "Content-Type: application/json" \
     -d '{"customer_slug": "touchbistro"}'
   ```

## Architecture

```
config/customers/*.yaml     ← Your extraction schemas (the customization point)
        ↓
src/call_chunker.py         ← Builds Claude prompt from YAML, extracts structured data
src/transcript_parser.py    ← Normalizes Gong JSON / raw text / CSV
src/gong_client.py          ← Gong API integration
        ↓
api/                        ← FastAPI backend (CRUD, search, analytics)
api/models.py               ← PostgreSQL models (Call, CallChunk, CallField)
        ↓
web/                        ← Next.js frontend (dashboard, call detail, analytics)
```

### Key Design Decisions

- **JSONB for chunk content** — each customer has different fields, JSONB stays flexible while remaining queryable
- **YAML configs** — more readable than JSON, supports comments, easy for non-technical users to edit
- **Dynamic prompt construction** — adding a new extraction field = editing YAML, zero code changes
- **EAV pattern for CallField** — extracted fields stored as rows so they're queryable via SQL regardless of schema

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/calls` | GET | List all calls |
| `/api/v1/calls` | POST | Create a call (paste transcript) |
| `/api/v1/calls/upload` | POST | Upload transcript file |
| `/api/v1/calls/{id}` | GET | Get call with chunks and fields |
| `/api/v1/calls/{id}/chunk` | POST | Process call through chunker |
| `/api/v1/calls/sync/gong` | POST | Sync calls from Gong API |
| `/api/v1/chunks/search` | POST | Search calls by text + field filters |
| `/api/v1/chunks/search/quotes` | GET | Search across extracted quotes |
| `/api/v1/schemas` | GET | List customer schemas |
| `/api/v1/schemas/{slug}` | GET/PUT | Get/update a schema |
| `/api/v1/analytics/overview` | GET | Aggregate analytics |
| `/api/v1/analytics/pain-points` | GET | Pain point frequency |
| `/api/v1/analytics/competitors` | GET | Competitor mention frequency |
| `/api/v1/analytics/deal-likelihood` | GET | Deal likelihood distribution |
| `/api/v1/analytics/sentiment` | GET | Sentiment distribution |

## Running Tests

```bash
pip install pytest
pytest tests/
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for chunking |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GONG_API_KEY` | No | Gong API key (for sync) |
| `GONG_API_SECRET` | No | Gong API secret (for sync) |
| `ALLOWED_ORIGINS` | No | CORS origins (default: http://localhost:3000) |
| `DEFAULT_CUSTOMER` | No | Default customer slug |
| `CLAUDE_MODEL` | No | Model to use (default: claude-sonnet-4-20250514) |
