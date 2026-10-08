# ADAPT — Autonomous D2C Ad Intelligence Engine

ADAPT is a full-stack autonomous advertising optimisation system. It continuously ingests multi-platform ad spend, sales, and behavioural data, detects ROAS anomalies, attributes root causes, scores opportunities, generates LLM-powered recommendations, executes budget reallocations, and learns from outcomes — without manual intervention.

---

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐    ┌──────────┐
│   Ingest    │───▶│   Diagnose   │───▶│    Optimise    │───▶│   Execute    │───▶│   Learn  │
│  reconciler │    │ anomaly z-   │    │ causal drivers │    │ ad platform  │    │ feedback │
│  CSV/API    │    │ score detect │    │ opp scoring    │    │ API calls    │    │ uplift   │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘    └──────────┘
                          │                    │
                          └──────┬─────────────┘
                                 ▼
                        ┌────────────────┐
                        │  LLM Agent     │
                        │  (OpenRouter)  │
                        │  narrative +   │
                        │  recommendations│
                        └────────────────┘
                                 │
                        ┌────────────────┐
                        │  FastAPI       │
                        │  in-memory     │
                        └────────────────┘
                                 │
                        ┌────────────────┐
                        │  index.html    │
                        │  Dashboard UI  │
                        └────────────────┘
```

**Stack:** Python 3.11 · FastAPI · Pandas/NumPy/SciPy · Scikit-learn · OpenRouter (nvidia/nemotron) · In-memory store · Native C NN (optional) · Vanilla JS frontend

---

## Quickstart

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY

# 4. Generate mock data
python scripts/generate_mock_data.py

# 5. Start the backend
uvicorn app.main:app --reload --port 8000

# 6. Open the dashboard
# Just open index.html in your browser — no build step needed
# Set API URL to http://localhost:8000 and click ▶ Run Loop
```

Or with Make:

```bash
make install   # pip install
make data      # generate mock CSVs
make run       # start uvicorn
```

Interactive API docs: `http://localhost:8000/docs`

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|---|---|---|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM reasoning | Yes |
| `LLM_MODEL` | Model slug, e.g. `nvidia/nemotron-3.5-lightning:free` | Yes |
| `LLM_PROVIDER` | `openrouter` | Yes |
| `META_ACCESS_TOKEN` | Meta Graph API token for live execution | Optional |
| `GOOGLE_ADS_TOKEN` | Google Ads API token | Optional |
| `NN_LIBRARY_PATH` | Path to compiled `libnn.so` | Optional |
| `INGEST_INTERVAL_MINUTES` | Background ingest cadence (default 5) | No |
| `DIAGNOSE_INTERVAL_MINUTES` | Background diagnose cadence (default 10) | No |

> The API key is **never** sent to the frontend. The dashboard calls `/llm/analyse` on the backend, which proxies to OpenRouter server-side.

---

## Project Structure

```
adapt/
├── app/
│   ├── config.py              # Pydantic settings — reads from .env
│   ├── database.py            # In-memory store for events, recommendations, executions, feedback
│   ├── main.py                # FastAPI app, scheduler, CORS, router registration
│   ├── schemas.py             # Pydantic request/response models
│   ├── ingestion/
│   │   ├── loader.py          # CSV loaders for all data sources
│   │   └── reconciler.py      # Merges sources → unified (date, platform, sku) frame
│   ├── intelligence/
│   │   ├── anomaly.py         # Rolling z-score anomaly detection per entity
│   │   ├── causal.py          # Driver correlation inference (Pearson + partial)
│   │   ├── scoring.py         # Opportunity scoring — native C NN or logistic fallback
│   │   └── llm_agent.py       # OpenRouter/Gemini/OpenAI reasoning proxy
│   ├── execution/
│   │   ├── decision_engine.py # Orchestrates diagnose → reason → persist recs
│   │   └── ad_apis.py         # Meta + Google Ads API wrappers
│   ├── learning/
│   │   └── feedback.py        # Records pre/post ROAS uplift outcomes
│   └── routers/
│       ├── ingest.py          # POST /ingest/run, GET /ingest/summary
│       ├── diagnose.py        # POST /diagnose/run, POST /diagnose/full
│       ├── execute.py         # GET /execute/recommendations, POST /execute/run
│       ├── feed.py            # GET /feed/events, POST /feed/feedback
│       └── llm.py             # POST /llm/analyse (key-safe LLM proxy)
├── data/
│   ├── ad_spend.csv           # Platform · campaign · SKU · spend · impressions · clicks
│   ├── sales.csv              # Platform · SKU · units sold · revenue
│   ├── ga_events.csv          # Channel · SKU · sessions · add_to_cart · purchases
│   ├── inventory.csv          # SKU · inventory_units
│   └── sku_margins.csv        # SKU · margin_pct
├── scripts/
│   ├── generate_mock_data.py  # Generates realistic 45-day mock CSVs
│   └── build_nn.sh            # Compiles native/nn.c → native/libnn.so
├── native/                    # Compiled C shared library (gitignored)
├── index.html                 # Single-file dashboard — no build step
├── requirements.txt
├── Makefile
└── .env.example
```

---

## API Reference

### Ingest
| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest/run` | Load CSVs, reconcile, return summary |
| `GET` | `/ingest/summary` | Stats on current unified dataset |

### Diagnose
| Method | Path | Description |
|---|---|---|
| `POST` | `/diagnose/run` | Anomaly detection only |
| `POST` | `/diagnose/full` | Full pipeline: anomalies + drivers + LLM narrative + recommendations |

### Execute
| Method | Path | Description |
|---|---|---|
| `GET` | `/execute/recommendations` | All stored recommendations |
| `POST` | `/execute/run` | Execute a recommendation (live or dry-run) |

### Feed
| Method | Path | Description |
|---|---|---|
| `GET` | `/feed/events` | Recent engine event log |
| `POST` | `/feed/feedback` | Log pre/post ROAS outcome for an execution |

### LLM
| Method | Path | Description |
|---|---|---|
| `POST` | `/llm/analyse` | Server-side LLM proxy — accepts anomalies + drivers, returns narrative + recommendations |

### Simulate
| Method | Path | Description |
|---|---|---|
| `POST` | `/simulate/loop` | Full ingest → diagnose → execute → feedback in one call |

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{ status: "ok" }` |

---

## Intelligence Pipeline

### 1. Ingest (`app/ingestion/reconciler.py`)
Loads five CSV sources and reconciles them at `(date, platform, sku)` grain. Derives: `roas`, `cpa`, `cvr`, `gross_margin`, `contribution`, `stockout_risk`. Validates required columns and fails fast with actionable messages.

### 2. Anomaly Detection (`app/intelligence/anomaly.py`)
Per entity, computes a 3-period rolling mean and std, then calculates a z-score against the most recent value. Entities with `|z| ≥ 2.0` are flagged. `|z| ≥ 3.0` = critical. Results sorted by absolute z-score.

### 3. Causal Attribution (`app/intelligence/causal.py`)
For each flagged entity, computes Pearson correlation between candidate drivers (`cvr`, `cpa`, `sessions`, `inventory_units`) and ROAS over the entity's history. Returns ranked driver list.

### 4. Opportunity Scoring (`app/intelligence/scoring.py`)
Scores every `(platform, sku)` pair using a weighted combination of conversion probability, margin, and stockout safety. Conversion probability uses a native C neural network (`libnn.so`) if compiled, otherwise falls back to logistic regression with the same weights.

### 5. LLM Reasoning (`app/intelligence/llm_agent.py`)
Sends anomalies, drivers, and top opportunities as structured JSON to the configured LLM provider. Returns a plain-text narrative and a ranked list of recommendations with action, entities, budget delta, confidence, and rationale. Falls back to a deterministic heuristic if the LLM call fails.

### 6. Execution (`app/execution/ad_apis.py`)
Wraps Meta Graph API and Google Ads API. In dry-run mode, simulates the call and returns a `simulated` status. In live mode, issues the actual budget change request.

### 7. Learning (`app/learning/feedback.py`)
Records pre/post ROAS values against an execution, computes `uplift = (post - pre) / pre * 100`, and persists to `outcome_feedback`. This data feeds back into the next loop's context for the LLM.

---

## Dashboard (`index.html`)

A single-file vanilla JS dashboard — no bundler, no framework, no build step.

| Section | What it shows |
|---|---|
| 01 Overview | KPI tiles: rows analysed, anomalies, pending actions, executed, avg confidence |
| 02 Signals | LLM engine briefing + causal driver correlation bars |
| 03 Anomalies & Opportunities | Per-entity anomaly list with z-score bars + top opportunity scores |
| 04 Recommendations | Recommendation table with simulate/execute buttons |
| 05 Activity | Execution log with outcome logging · data coverage · event stream |
| 06 Agent Pipeline | Live status of all 5 agent stages with running/ready indicators |
| 07 Loop History | Canvas line chart of ROAS by entity across loops + delta tiles |

**Demo mode:** Toggle on to run entirely in-browser with mock data. Calls `/llm/analyse` on the backend for live LLM reasoning even in demo mode (falls back to hardcoded data if backend is unreachable).

**Dry-run mode:** On by default. Simulates execution without hitting real ad platform APIs.

---

## Storage

All data (events, recommendations, executions, feedback) is stored in-memory in `app/database.py`. State resets on server restart. This is intentional — ADAPT is a decision engine, not a database. If you need persistence, the store interface is simple enough to swap for SQLite or any other backend.

---

## Native C Neural Network (Optional)

```bash
make nn
# Compiles native/nn.c → native/libnn.so
# Set NN_LIBRARY_PATH=./native/libnn.so in .env
```

The default C implementation is a logistic scorer with the same weights as the Python fallback. Replace the body of `score_conversion()` in `native/nn.c` with your own model and recompile.

---

## Background Scheduler

On startup, APScheduler registers two jobs:

- **Ingest** — runs every `INGEST_INTERVAL_MINUTES` (default 5)
- **Diagnose** — runs every `DIAGNOSE_INTERVAL_MINUTES` (default 10)

Both are fire-and-forget; failures are logged but do not crash the server.

---

## Development

```bash
# Lint
ruff check app/

# Format
ruff format app/

# Type check
mypy app/

# Clean pycache
make clean
```

---

## Roadmap

- [ ] WebSocket push for real-time dashboard updates
- [ ] TikTok Ads API integration
- [ ] Amazon Ads API integration
- [ ] Time-series forecasting for proactive budget shifting
- [ ] Multi-tenant support with per-account data isolation
- [ ] Reinforcement learning feedback loop replacing heuristic confidence scores
