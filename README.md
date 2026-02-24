# Gong Call Chunker

Turn sales call transcripts into structured, searchable data. Tell the system what you care about (restaurant size, pain points, competitors, deal stage) and it extracts that from every call automatically.

**Built for GTM teams.** No coding required to use it — just paste a transcript and click "Chunk."

---

## What Does It Actually Do?

You paste (or sync from Gong) a sales call transcript. The system reads it and pulls out:

- **Structured fields** you define — restaurant type, company size, pain points, competitors, buying stage, whatever matters to your sales process
- **Discussion topics** — the 5-8 major things talked about, with timestamps
- **Key insights** — specific customer signals within each topic (sentiment, action items)
- **Verbatim quotes** — the exact words prospects used, tagged by theme
- **Call summary** — overall sentiment, deal likelihood (1-10), next steps

All of this is searchable and shows up in analytics dashboards. Want to know which pain point comes up most? Which competitor gets mentioned? What the average deal likelihood is across all calls this month? It's all there.

---

## Two Ways to Get Started

### Option A: Someone hosts it for you (Non-technical users)

If someone on your team (or a vendor) has already deployed this, you just need:

1. **A URL** — something like `https://calls.yourcompany.com`
2. **An API key** — you'll get this from whoever set it up

That's it. Open the URL in your browser. You'll see a dashboard. From there you can:

- **Upload calls** — Click "Upload Transcript," paste the text, pick your customer config, click Upload
- **Chunk calls** — Click into any call, hit "Chunk This Call," wait ~30 seconds
- **Search** — Search across all calls by keyword or filter by any extracted field
- **View analytics** — See pain point frequency, competitor mentions, deal likelihood trends

No terminal, no code, no Docker. Just a web app.

---

### Option B: Run it yourself (Technical setup)

This is for the person on the team who's going to set it up. Takes about 15 minutes.

#### What you need installed first

You need three things on your computer. If you don't have them, here's how to get each one:

**1. Docker Desktop** (runs the database)
- Go to https://www.docker.com/products/docker-desktop/
- Download for your operating system (Mac or Windows)
- Open the installer and follow the prompts
- Once installed, open Docker Desktop — you'll see a whale icon in your menu bar. That means it's running.

**2. Python 3.9+** (runs the backend)
- **Mac:** Open Terminal (search "Terminal" in Spotlight). Type `python3 --version`. If you see a version number, you're good. If not, go to https://www.python.org/downloads/ and install it.
- **Windows:** Go to https://www.python.org/downloads/ and install. Make sure to check "Add Python to PATH" during install.

**3. Node.js 18+** (runs the frontend)
- Go to https://nodejs.org/ and download the LTS version
- Run the installer

**4. A Claude API key**
- Go to https://console.anthropic.com/
- Create an account (or sign in)
- Go to API Keys and create one
- Copy it — you'll need it in the next step

#### Step-by-step setup

Open your terminal (Mac: search "Terminal" in Spotlight. Windows: search "Command Prompt" or "PowerShell").

```bash
# 1. Download the code
git clone https://github.com/spartacus3131/gong-call-chunker.git
cd gong-call-chunker

# 2. Create your config file
cp .env.example .env
```

Now open the `.env` file in any text editor (TextEdit, Notepad, VS Code — anything works). Find this line:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Replace `sk-ant-...` with your actual Claude API key. Save the file.

```bash
# 3. Start the database
docker compose up db -d

# 4. Install Python dependencies
pip3 install -r requirements.txt

# 5. Set up the database tables
alembic upgrade head

# 6. Load sample data (3 example TouchBistro sales calls)
python3 scripts/seed_sample.py

# 7. Start the API server
uvicorn api.main:app --reload --port 8000
```

Open a **second terminal window** (don't close the first one):

```bash
# 8. Start the web interface
cd gong-call-chunker/web
npm install
npm run dev
```

Now open your browser and go to **http://localhost:3000**

You should see a dashboard with 3 sample calls. Click one, hit "Chunk This Call," and watch it extract structured data.

#### Stopping it

- Press `Ctrl+C` in both terminal windows to stop the servers
- Run `docker compose down` to stop the database
- To start again later, just repeat steps 3, 7, and 8

---

## Customizing What Gets Extracted

This is the most important part. The system extracts whatever you tell it to extract, defined in a simple config file.

The config for TouchBistro POS is included as an example at `config/customers/touchbistro.yaml`. It extracts things like restaurant size, type, pain points, current POS system, competitor mentions, etc.

### Creating your own config

Create a new file in `config/customers/`. For example, `config/customers/acme-crm.yaml`:

```yaml
customer: acme_crm
display_name: "Acme CRM"
industry: crm_software

extraction_schema:
  fields:
    # Define each piece of info you want extracted from calls
    - name: company_size
      type: enum
      options: [startup, smb, mid_market, enterprise]
      description: "Size of the prospect's company"

    - name: industry
      type: text
      description: "What industry the prospect is in"

    - name: current_crm
      type: text
      description: "CRM they're currently using (Salesforce, HubSpot, etc.)"

    - name: pain_points
      type: list
      description: "Specific pain points mentioned"
      examples: [bad_reporting, slow_onboarding, poor_mobile, too_expensive]

    - name: team_size
      type: integer
      description: "Number of sales reps who would use the CRM"

    - name: budget_mentioned
      type: boolean
      description: "Did they discuss budget or pricing?"

    - name: competitor_mentions
      type: list
      description: "Other CRM tools mentioned"

    - name: buying_stage
      type: enum
      options: [early_research, evaluating, decision_ready, negotiating]
      description: "Where they are in the buying process"

  # These control how the call is broken into sections (usually leave as-is)
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

**No code changes needed.** Save the file, and it immediately appears in the web UI's customer dropdown.

### Field types reference

| Type | What it extracts | Example value |
|------|-----------------|---------------|
| `enum` | One value from a list you define | `"fine_dining"` |
| `text` | Any text | `"They're using Square POS"` |
| `integer` | A number | `3` |
| `boolean` | Yes or No | `true` |
| `list` | Multiple values | `["scheduling", "reporting", "inventory"]` |

---

## Connecting to Gong (Optional)

Instead of manually pasting transcripts, you can pull them directly from Gong.

1. In Gong, go to **Settings > API** and get your API key and secret
2. Add them to your `.env` file:
   ```
   GONG_API_KEY=your-key-here
   GONG_API_SECRET=your-secret-here
   ```
3. Sync calls:
   ```bash
   python3 scripts/sync_gong.py --customer touchbistro --from 2026-01-01
   ```

This pulls all calls from that date forward, stores the transcripts, and makes them ready to chunk.

---

## For Production / Sharing With Your Team

If you want your whole team to use this (not just locally on your machine):

### Deploy to Railway (easiest)

[Railway](https://railway.app) can run this with one click:

1. Push this repo to your GitHub
2. Connect Railway to your GitHub repo
3. Railway auto-detects the Dockerfile and sets up Postgres
4. Add your `ANTHROPIC_API_KEY` and `API_KEYS` in Railway's environment variables
5. Share the URL with your team

### Security

Set `API_KEYS` in your environment to enable authentication:
```
API_KEYS=your-secret-key-1,another-key-for-someone-else
```

When set, every API request needs an `X-API-Key` header. The web frontend will need to be configured to include this.

When `API_KEYS` is **not** set (default), auth is disabled — fine for local development, not for production.

---

## API Reference

For developers building integrations:

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/api/v1/calls` | GET | List all calls |
| `/api/v1/calls` | POST | Create a call (paste transcript) |
| `/api/v1/calls/upload` | POST | Upload a transcript file |
| `/api/v1/calls/{id}` | GET | Get a call with all extracted data |
| `/api/v1/calls/{id}/chunk` | POST | Process a call through the AI chunker |
| `/api/v1/calls/sync/gong` | POST | Pull calls from Gong |
| `/api/v1/chunks/search` | POST | Search across calls |
| `/api/v1/chunks/search/quotes` | GET | Search extracted quotes |
| `/api/v1/schemas` | GET | List customer configs |
| `/api/v1/schemas/{slug}` | GET/PUT | View or edit a config |
| `/api/v1/analytics/overview` | GET | Dashboard stats |
| `/api/v1/analytics/pain-points` | GET | Pain point frequency |
| `/api/v1/analytics/competitors` | GET | Competitor mentions |
| `/api/v1/analytics/deal-likelihood` | GET | Deal score distribution |
| `/api/v1/analytics/sentiment` | GET | Call sentiment breakdown |

Full interactive API docs at `http://localhost:8000/docs` when running locally.

---

## Troubleshooting

**"Docker is not running"** — Open Docker Desktop and wait for the whale icon to appear in your menu bar.

**"command not found: python3"** — Python isn't installed. See the installation links above.

**"Chunking failed"** — Check that your `ANTHROPIC_API_KEY` is set correctly in `.env`. You can verify at https://console.anthropic.com/.

**"Connection refused on port 5432"** — The database isn't running. Run `docker compose up db -d` first.

**"Module not found"** — Run `pip3 install -r requirements.txt` again.

**Call is stuck on "Processing"** — The Claude API call may have timed out. Refresh the page — if it shows "Failed," click "Retry Chunking."
