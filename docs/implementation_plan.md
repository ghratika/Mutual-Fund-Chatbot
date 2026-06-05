# Phase-Wise Implementation Plan: Mutual Fund FAQ Assistant

This document outlines the step-by-step roadmap for developing and deploying the **Mutual Fund FAQ Assistant**. The implementation is divided into **7 structural phases**, progressing from ingestion and database setup to retrieval logic, guardrails, scheduling, and UI development.

---

## Roadmap at a Glance

| Phase | Milestone | Focus Area | Estimated Effort |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Ingestion & Scraping | Data harvesting from 5 Groww URLs | 2-3 Days |
| **Phase 2** | Database & Embeddings | ChromaDB schema setup & vector generation | 1-2 Days |
| **Phase 3** | Intent Router & Refusals | Query classification & advisory block gates | 2 Days |
| **Phase 4** | RAG Search & Prompting | Hybrid retrieval & facts-only context building | 2 Days |
| **Phase 5** | Generation & Guardrails | LLM integration & programmatic post-validation | 2 Days |
| **Phase 6** | Automation & Scheduler | Daily cron execution for updating NAV/metrics | 1 Day |
| **Phase 7** | Frontend Chat Interface | Streamlit interface with sticky disclaimers | 2 Days |

---

## Phase 1: Ingestion & Scraping Setup
*Goal: Harvest structured and unstructured mutual fund data from the 5 designated Groww URLs.*

- [x] **1.1 Scraper Architecture**
  - Develop a scraper module (`scraper.py`) using `BeautifulSoup` (or `Playwright` if React hydration requires JS execution).
  - Configure target headers and delay mechanisms to prevent rate-limiting.
- [x] **1.2 Dual-Representation Parsing**
  - Write standard regex/DOM selectors to extract exact quantitative parameters:
    - Scheme Name, Category, NAV, Expense Ratio, Exit Load, Minimum SIP, Riskometer Classification, Benchmark Index.
    - Fund Management Data: Manager names, tenure, and background text.
  - Extract unstructured text sections (e.g. Investment Objective, Scheme Description).
- [x] **1.3 Data Serialization**
  - Output scraped data into a structured schema (`data/corpus.json`) for validation prior to embedding.

> [!NOTE]
> Since the mutual fund schemes are fixed to 5 specific URLs, the ingestion engine must raise alert flags if any selector fails to parse a required quantitative field.

---

## Phase 2: Database & Embeddings Setup
*Goal: Store corpus representations into a local ChromaDB database with metadata indices.*

- [x] **2.1 Chunker Implementation (Entity-Based Mapping)**
  - Rather than standard character-level splitting (which randomly slices structured fields), develop `chunker.py` using a **Deterministic Entity Chunker** that maps each fund record in `corpus.json` into three distinct, self-contained semantic text chunks:
    1. **Core Metrics Chunk**: Formats scheme name, NAV, NAV date, expense ratio, exit load, min SIP, riskometer, and benchmark into a single structured text statement.
    2. **Scheme Description Chunk**: Maps the fund's investment objective and philosophy text.
    3. **Fund Manager Profiles Chunks**: Generates 1 individual chunk per fund manager containing their name, experience, education, tenure date, and count of managed funds.
  - Inject metadata (`scheme_name`, `url`, and `chunk_type`) into every chunk to support strict query pre-filtering.
- [x] **2.2 Embedding Generator (BGE Small Model)**
  - Configure the embedding pipeline using the **BGE Small (`BAAI/bge-small-en-v1.5`)** model via the `sentence-transformers` library, which generates highly dense 384-dimensional vectors optimal for short factual chunks with sub-millisecond latencies.
- [x] **2.3 Vector Database Initialization (ChromaDB Integration)**
  - Initialize a local, persistent **ChromaDB** client (`db_manager.py`) storing vectors inside the `db/` workspace folder.
  - Define the collection schema and write indexing rules for metadata attributes (`scheme_name`, `url`, and `chunk_type`) to enable deterministic query pre-filtering and prevent cross-talk.
  - Implement idempotent upsert operations to ensure daily scheduler updates run safely without bloat.

---

## Phase 3: Intent Classification & Refusal Engine
*Goal: Intercept and block subjective or advisory queries before triggering LLM generation.*

- [x] **3.1 Query Classification System**
  - Implement a rule-based, heuristic, and semantic classification model (`intent_classifier.py`):
    - **FACTUAL**: Valid queries about fund parameters and profiles, as well as basic greetings.
    - **ADVISORY**: Queries asking for advice, comparative opinions, or safety assessments.
    - **OUT_OF_SCOPE**: Queries with no financial or mutual fund keywords (e.g., unrelated questions).
- [x] **3.2 Refusal Routing Engine**
  - Route queries through a multi-tier gate system (Greetings -> Out-Of-Scope Heuristic -> Rule-based Advisory checks -> Semantic similarity checks).
  - Return compliance-approved refusal responses (with SEBI/AMFI educational links for advisory queries, and scope-correction suggestions for out-of-scope queries).

---

## Phase 4: Retrieval & Context Construction
*Goal: Execute hybrid semantic searches while preventing information "cross-talk" between funds.*

- [x] **4.1 Deterministic Pre-Filtering**
  - Extract the specific fund keyword from the query (e.g., "HDFC Defence" $\rightarrow$ `HDFC Defence Fund`).
  - Apply metadata filter `where={"scheme_name": "HDFC Defence Fund Direct Growth"}` inside ChromaDB queries.
- [x] **4.2 Hybrid Retrieval Engine**
  - Merge semantic vector similarity search results with keyword matching (BM25) to guarantee specific words like "exit load" trigger correct context chunks.
- [x] **4.3 Prompt Context Builder**
  - Assemble retrieved text chunks alongside raw metrics from the structured store into a clean prompt schema.

---

## Phase 5: LLM Generation & Programmatic Guardrails
*Goal: Interface with Groq LLM and enforce strict structural compliance on answers.*

- [x] **5.1 Prompt Engineering**
  - Develop system prompt (`prompts.py`) dictating:
    - Answer must rely *only* on context. No extrapolation.
    - No investment tips or recommendations.
    - Strict formatting constraints.
- [x] **5.2 Programmatic Post-Validator**
  - Write a validator script (`guardrails.py`) wrapping the LLM response:
    - Programmatically count sentences to ensure it is $\le 3$.
    - Verify that exactly one citation link from the 5 original URLs is included.
    - Standardize and append the footer: `"Last updated from sources: <date>"`.

> [!IMPORTANT]
> If a response fails any post-validation check, the engine should run a fallback handler (e.g., re-prompting the LLM or falling back to a structured template) to ensure compliance.

---

## Phase 6: Automation & Scheduler
*Goal: Automate daily ingestion to handle market fluctuations (e.g. NAV changes).*

- [x] **6.1 Execution Wrapper**
  - Build a single-point command line pipeline (`run_ingestion.py`) that executes scraping, parses metrics, generates embeddings, and updates the local ChromaDB database.
- [x] **6.2 Scheduler Setup**
  - Implement scheduling mechanism to run at 10:00 AM IST daily (implemented as a local-time system scheduler loop in `run_ingestion.py` that sleeps precisely until 10:00 AM IST every day).
  - Re-triggers the full scraping, embedding, and vector database update pipeline.

---

## Phase 7: Frontend Chat Interface
*Goal: Create a clean, premium, and easy-to-use user experience.*

- [x] **7.1 React & Vite Frontend with FastAPI Backend**
  - Develop `frontend/` React SPA utilizing a modern glassmorphic, dark-mode style theme as specified in the `stitch` guidelines.
  - Implement a sticky warning disclaimer banner at the top of the viewport.
- [x] **7.2 Interactive Enhancements**
  - Render the three recommended quick-start question buttons.
  - Format response outputs nicely; display citation source links as modern clickable badge icons.
