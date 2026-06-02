# Personal Finance Assistant

An AI-driven, multi-user personal finance companion built with FastAPI, Next.js, and Groq LLM.

**Live demo:** Run locally (see setup instructions below)  
**GitHub:** https://github.com/salmanshahidmalik/finance-assistant

---

## What's Built

### Core Features
- ✅ Multi-user authentication via Clerk
- ✅ CSV transaction import with data cleaning and deduplication
- ✅ Conversational AI assistant powered by Groq (Llama 3.3 70B)
- ✅ Intent routing — different query types handled differently
- ✅ Spending queries ("How much did I spend on groceries?")
- ✅ Time comparisons ("Am I spending more than usual?")
- ✅ Recurring subscription detection
- ✅ Unusual activity / pattern detection
- ✅ Budget tracking with visual progress bars
- ✅ User memory ("I get paid on the 1st")
- ✅ Merchant lookup via Tavily web search
- ✅ Financial summaries in plain English
- ✅ Spending reduction suggestions

### Stubbed / Simplified
- **Receipt vision:** Groq does not support image input. The endpoint accepts image uploads but returns a prompt asking the user to type details manually. With a vision-capable model (Claude, GPT-4o, Gemini Pro), this would be a one-line model swap.
- **Real bank integration:** Uses CSV import instead of Plaid/Open Banking OAuth. The import pipeline is production-ready (handles messy data, duplicates, multiple formats).
- **Push notifications:** Budget warnings appear in chat but are not pushed via email/SMS.
- **Embeddings/pgvector:** The schema includes a vector column but embeddings are not computed. For the current dataset size, passing transactions directly as JSON context is fast and accurate enough. At 100k+ transactions, a RAG pipeline over pre-computed embeddings would replace this.

---

## Architecture
User message
↓
Intent Router (Llama 3.1 8B — fast, cheap classification)
↓
┌─────────────────────────────────────────────────┐
│ simple_lookup    → recent transactions → 70B    │ ~500ms
│ time_comparison  → monthly_stats → 70B          │ ~1s
│ pattern_detection→ 200 transactions → 70B       │ ~1.5s
│ budget_query     → budgets + stats → 8B         │ ~500ms
│ memory_update    → extract KV → upsert → 8B     │ ~300ms
│ merchant_lookup  → Tavily search → 8B           │ ~2s
│ general_summary  → stats + recent → 70B         │ ~1.5s
└─────────────────────────────────────────────────┘
↓
Response streamed to user

### Stack
| Layer | Technology | Reason |
|---|---|---|
| Backend | FastAPI (Python) | Async, clean, easy tool integration |
| Frontend | Next.js 14 (TypeScript) | Fast to build, great DX |
| Auth | Clerk | Commodity — not worth building |
| Database | Supabase (Postgres) | Free, pgvector ready, no infra |
| LLM | Groq (Llama 3.3 70B) | Free tier, very fast inference |
| Web search | Tavily | Designed for LLM agents |

---

## Key Architectural Decisions

### 1. Intent routing — the most important decision
Every query is first classified by a small fast model (Llama 3.1 8B) into one of 8 intent categories. Each category gets a different handler with different data retrieval and model selection.

**Why this matters:** A naive implementation sends every message to the biggest model with the full transaction history pasted as context. This is slow, expensive, and doesn't scale. A simple spending lookup doesn't need 200 transactions and a 70B model — it needs 50 recent transactions and a fast model. Routing by intent means:
- Simple queries: ~300ms, cheap
- Complex queries: ~1.5s, more expensive but justified
- The system degrades gracefully — if a query is misclassified, it falls back to `general_summary`

### 2. Pre-aggregated monthly stats
Every CSV import recomputes a `monthly_stats` table (year_month + category + total + count). Time comparison queries (`am I spending more than usual?`) hit this table directly instead of scanning all transactions.

**Why:** A user with 3 years of daily transactions has ~1000+ rows. Scanning all of them for a trend query is wasteful. Pre-aggregation makes these queries instant regardless of history length. This is the pattern used by every production analytics system.

### 3. Data cleaning on import
The CSV importer handles: inconsistent column names, multiple amount formats (`$50`, `(50.00)`, `-50`), multiple date formats, missing fields, duplicate rows (fuzzy dedup on date + amount + merchant). Real transaction exports are messy — this is not optional.

### 4. User memory
A simple key-value table (`user_context`) stores preferences extracted from natural language. Every system prompt is prefixed with the user's saved context. This means "I get paid on the 1st" said once is applied to all future responses.

### 5. Buy vs build
- Auth: Clerk (20 minutes, never touched again)
- Database: Supabase (Postgres + pgvector + storage in one)
- LLM: Groq API (no GPU infra)
- Search: Tavily (built for LLM agents)

Time saved on commodity work was spent on the routing logic, data pipeline, and query handlers — the genuinely hard parts.

---

## Handling Large Data

The current implementation works well for the sample dataset. For 10x-100x data:

- **monthly_stats table** already handles trend queries at any scale — O(months) not O(transactions)
- **simple_lookup** passes last 100 transactions — sufficient for most queries, bounded cost
- **pattern_detection** passes last 200 transactions — would need pagination at very large scale
- **Next step:** Compute embeddings on import, use pgvector similarity search to retrieve only relevant transactions for each query instead of passing recent N rows

---

## What I Would Build Next

1. **Receipt vision** — swap Groq for Claude/GPT-4o for the vision handler, already stubbed
2. **Streaming responses** — FastAPI SSE + Next.js ReadableStream for faster perceived latency
3. **Anomaly detection** — Z-score per category per user, flag outliers automatically
4. **Plaid integration** — replace CSV import with real bank OAuth
5. **Budget alerts** — background job checking budgets daily, email/push when near limit
6. **Embeddings pipeline** — nightly job to embed new transactions, pgvector retrieval

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase account
- Clerk account
- Groq API key (free)
- Tavily API key (free)

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install fastapi uvicorn python-dotenv groq supabase pandas python-multipart pillow tavily-python pydantic httpx
```

Create `backend/.env`:
```env
GROQ_API_KEY=your_groq_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
CLERK_SECRET_KEY=your_clerk_secret
TAVILY_API_KEY=your_tavily_key
```

Run Supabase SQL (see `backend/schema.sql`):
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
```

```bash
npm run dev
```

Open http://localhost:3000

---

## Trade-offs and Limitations

| Decision | Trade-off |
|---|---|
| Groq (free) over Claude/GPT-4o | No vision support for receipts |
| JSON context over RAG | Simpler but won't scale past ~500 transactions per query |
| CSV import over Plaid | No real-time sync, manual upload required |
| Pre-aggregated stats | Fast queries but requires recompute on every import |
| Clerk for auth | Vendor dependency, but saves days of work |

---

## Time Breakdown

This project was built with more time than the suggested 6-hour window. With a strict 6-hour constraint I would have:
- Built the intent router and simple_lookup handler fully
- Stubbed time_comparison with a basic monthly total query
- Skipped merchant_lookup and receipt vision entirely
- Written a simpler frontend with just the chat interface
- Focused the README on explaining the routing decision in depth

The routing architecture, data cleaning pipeline, and pre-aggregated stats are the decisions I would defend regardless of time available — they are what separate a demo from something that could actually ship.