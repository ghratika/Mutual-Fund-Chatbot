# 💰 Mutual Fund RAG Chatbot

A **facts-only FAQ chatbot** for HDFC Mutual Fund schemes, powered by a Retrieval-Augmented Generation (RAG) pipeline. The assistant answers objective, verifiable queries about mutual funds using data scraped from official public sources — **without ever providing investment advice, opinions, or recommendations**.

> ⚠️ **Facts-only. No investment advice.**

---

## What It Does

- **Answers factual queries** about 5 HDFC Mutual Fund schemes — NAV, expense ratio, exit load, fund managers, SIP amounts, riskometer, benchmark index, and more.
- **Cites official sources** — every response includes a verifiable link from [Groww](https://groww.in).
- **Refuses advisory queries** — politely declines subjective questions like *"Should I invest?"* or *"Which fund is better?"* and redirects users to SEBI/AMFI educational resources.
- **Keeps data fresh** — a daily GitHub Actions cron job scrapes the latest fund data from Groww every morning at 10:00 AM IST.

---

## Schemes Covered

| # | Scheme | Category |
|---|--------|----------|
| 1 | HDFC Mid Cap Fund Direct Growth | Equity — Mid Cap |
| 2 | HDFC Large Cap Fund Direct Growth | Equity — Large Cap |
| 3 | HDFC Small Cap Fund Direct Growth | Equity — Small Cap |
| 4 | HDFC Gold ETF Fund of Fund Direct Plan Growth | Other — FoF (Domestic) |
| 5 | HDFC Defence Fund Direct Growth | Equity — Sectoral/Thematic |

All fund data is sourced from [Groww](https://groww.in) scheme pages.

---

## Architecture

The system consists of two pipelines:

### 1. Offline Ingestion Pipeline

Scrapes Groww mutual fund pages → extracts structured key-value metrics (NAV, expense ratio, etc.) and unstructured text (descriptions, fund manager profiles) → generates semantic chunks → embeds using BGE embeddings → stores in ChromaDB vector database.

### 2. Online Query Pipeline

```
User Query
    │
    ▼
Intent Classifier (BGE embeddings + regex rules)
    │
    ├── Advisory / Out-of-Scope → Polite refusal with SEBI/AMFI links
    │
    └── Factual → Hybrid Retrieval Engine
                      │
                      ├── Semantic search (ChromaDB cosine similarity)
                      ├── Keyword search (BM25 scoring)
                      └── Deterministic pre-filter by scheme name
                              │
                              ▼
                      Context Builder (raw metrics + retrieved chunks)
                              │
                              ▼
                      Groq LLM (llama-3.3-70b-versatile, temperature=0)
                              │
                              ▼
                      Guardrails Validation
                        • ≤ 3 sentences
                        • Exactly 1 citation URL
                        • "Last updated" footer
                              │
                              ▼
                      Response to User
```

### Key Design Decisions

- **Hybrid Retrieval**: Fuses 60% semantic similarity (cosine via BGE embeddings) with 40% BM25 keyword scoring to balance contextual relevance with exact-match precision.
- **Deterministic Pre-Filtering**: When a specific fund is mentioned in the query, ChromaDB searches are filtered by `scheme_name` metadata to prevent cross-talk between funds.
- **Multi-Layer Intent Classification**: Greeting override → financial keyword gate → regex-based advisory pattern matching → semantic similarity against advisory/factual anchor embeddings.
- **Template Fallback**: If the LLM response fails guardrail validation, a structured template response is generated directly from the scraped database metrics — guaranteeing compliance.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python, FastAPI, Uvicorn |
| Frontend | React 19, Vite 8, Lucide React |
| Vector Database | ChromaDB (local persistent) |
| Embeddings | BAAI/bge-small-en-v1.5 (sentence-transformers) |
| LLM | Groq Cloud API — llama-3.3-70b-versatile |
| Web Scraper | BeautifulSoup, Requests |
| Data Scheduler | GitHub Actions (daily cron) |

---

## Project Structure

```
Mutual-Fund-RAG-Chatbot/
│
├── scraper.py               # Scrapes fund data from Groww (5 schemes)
├── chunker.py                # Generates semantic chunks (metrics, descriptions, managers)
├── db_manager.py             # ChromaDB vector store manager with BGE embeddings
├── retrieval.py              # Hybrid retrieval engine (semantic + BM25 fusion)
├── intent_classifier.py      # Multi-layer intent classification
├── guardrails.py             # LLM response validation & template fallback
├── prompts.py                # System prompt for constrained LLM generation
├── server.py                 # FastAPI application (API endpoints)
├── run_ingestion.py          # Ingestion pipeline runner & daily scheduler
│
├── data/
│   └── corpus.json           # Scraped structured fund data (auto-updated daily)
├── db/                       # ChromaDB persistent storage (gitignored)
│
├── frontend/
│   └── src/
│       ├── App.jsx           # Main React chat interface
│       ├── App.css           # Component styles
│       └── index.css         # Global design system
│
├── .github/workflows/
│   └── daily-ingestion.yml   # GitHub Actions daily scraper cron
│
├── test_guardrails.py        # Guardrails unit tests
├── test_intent_classifier.py # Intent classifier unit tests
├── test_retrieval.py         # Retrieval engine unit tests
│
└── requirements.txt          # Python dependencies
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a user query, receive a cited factual response |
| `GET` | `/api/funds` | Returns basic info (NAV, AUM, category) for all 5 schemes |
| `GET` | `/health` | Health check — reports component readiness |

---

## Constraints & Compliance

| Rule | Details |
|------|---------|
| **No Investment Advice** | The system never provides buy/sell recommendations, comparisons, or return projections |
| **Max 3 Sentences** | Every factual response is capped at 3 sentences |
| **Single Citation** | Each response includes exactly one verifiable source URL |
| **No PII Collection** | No personal data (PAN, Aadhaar, phone, email) is collected or stored |
| **Official Sources Only** | Data sourced exclusively from Groww (backed by AMC/AMFI/SEBI data) |

---

## Known Limitations

- **Corpus limited to 5 HDFC schemes** — other AMCs and funds are not covered.
- **Data refreshes once daily** — intraday NAV changes are not reflected until the next cron run.
- **Scraper depends on Groww's page structure** — if Groww changes their `__NEXT_DATA__` hydration payload, the scraper will need updating.
- **LLM requires Groq API availability** — if the API is down or rate-limited, the system falls back to template-based responses built from scraped metrics.
- **Responses are intentionally brief** — max 3 sentences with a single citation, by design.

---

> **Facts-only. No investment advice.**
