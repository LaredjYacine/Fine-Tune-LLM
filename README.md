# Fine-Tune-LLM
This repository is me learning how to Fine Tune LLMs 
# Qwen2.5-1.5B PEFT LoRA Fine-Tuner

This project sets up and executes a Parameter-Efficient Fine-Tuning (PEFT) pipeline using **LoRA** (Low-Rank Adaptation) on the **Qwen/Qwen2.5-1.5B-Instruct** causal language model. It utilizes a subset of the Databricks Dolly 15k dataset formatted for instruction tuning via Hugging Face's `transformers`, `peft`, `datasets`, and `trl` libraries.

---

## Installation

You can install all required dependencies instantly using **uv**:

```bash
uv pip install transformers peft huggingface_hub torch torchao datasets trl
```
<p align="center">
  <img width="500" alt="Screenshot_1" src="https://github.com/user-attachments/assets/eb2d2ada-b468-4636-9da0-c0030a8b8054" />
</p>

# 🧠 AI Agent Backend — LangGraph + Celery + FastAPI

An asynchronous, production-style backend that exposes a **ReAct-style AI agent** (built with LangGraph + Ollama) through a **FastAPI** HTTP API, backed by **Celery** workers and **Upstash Redis** for task queuing, idempotency, and result caching. The agent can query a **Supabase** database, search **Wikipedia**, and perform basic calculations.

---

## 📐 Architecture

```
Client
  │
  ▼
FastAPI (app.py)
  │  - Rate limiting (5 req/min)
  │  - Idempotency key handling
  │  - Enqueues job to Celery
  ▼
Celery Worker (worker.py / Langraph.py)
  │  - Runs LangGraph ReAct agent
  │  - Model: qwen2.5:14b via Ollama
  │  - Tools: Supabase query, Wikipedia search, Calculator
  ▼
Upstash Redis
  │  - Message broker
  │  - Result backend
  │  - Idempotency + job-status cache
  ▼
Supabase (Postgres)
  - Agent-accessible database (Create + Read only)
```

---

## ✨ Features

- **LangGraph ReAct Agent** running locally via Ollama (`qwen2.5:14b`)
- **Tool-using agent** with access to:
  - `execute_supabase` — safely run whitelisted Supabase queries (destructive ops like `DELETE`/`DROP`/`TRUNCATE` are blocked)
  - `get_tables` / `get_schema` — introspect the Supabase database before writing queries
  - `Search` / `Search_page` — Wikipedia lookups for up-to-date information
  - `Calculator` — basic arithmetic (add, subtract, multiply, divide)
- **FastAPI service** with:
  - `/generate` — submit a prompt as an async job
  - `/status/{job_id}` — poll job status/result
  - Rate limiting via `slowapi` (5 requests/minute per client)
  - **Idempotency keys** to prevent duplicate job submission
- **Celery task queue** with automatic retries (exponential backoff) and a **Dead Letter Queue (DLQ)** for permanently failed jobs
- **JSON trace logging** of every LLM call and tool invocation (`agent_trace.jsonl`) for debugging/observability



## ⚙️ Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed locally (or accessible via network) with the `qwen2.5:14b` model pulled
- A [Supabase](https://supabase.com/) project (URL + API key)
- An [Upstash Redis](https://upstash.com/) instance (or any Redis-compatible broker)
- `zstd` (used during environment setup)

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
Supabase_Key=your-supabase-service-or-anon-key
supabase_url=https://your-project.supabase.co
UPSTASH_REDIS_REST_URL=redis://your-upstash-redis-url
```

> **Note:** `app.py` and `celery_app.py` read `UPSTASH_REDIS_REST_URL` directly as the Celery broker/backend URL, so make sure it's a valid Redis connection string (not just the REST API URL from the Upstash dashboard).

---

## 🚀 Installation

```bash
# Clone the repo
git clone  https://github.com/LaredjYacine/Fine-Tune-LLM.git
cd Fine-Tune-LLM

# Install Python dependencies
pip install langgraph langchain langchain-ollama wikipedia supabase
pip install fastapi uvicorn celery redis slowapi python-dotenv
pip install transformers torch accelerate

# Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &

# Pull the model used by the agent
ollama pull qwen2.5:14b
```

---

## ▶️ Running the Project

### 1. Start the Celery worker

```bash
celery -A celery_app worker --loglevel=info
```

### 2. Start the FastAPI server

```bash
uvicorn app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

---

## 📡 API Reference

### `POST /generate`

Submit a prompt to the agent. Runs asynchronously via Celery.

**Query parameter:**

| Name   | Type   | Required | Description                |
|--------|--------|----------|----------------------------|
| prompt | string | ✅       | The prompt for the agent   |

**Header (optional):**

| Name              | Description                                              |
|-------------------|------------------------------------------------------------|
| `idempotency_key` | Prevents duplicate submissions of the same logical request |

**Example:**

```bash
curl -X POST "http://127.0.0.1:8000/generate?prompt=What is the capital of France?" \
     -H "idempotency_key: my-unique-key-123"
```

**Response:**

```json
{
  "job_id": "a1b2c3d4-...",
  "status": "202 Accepted",
  "idempotency_key": "my-unique-key-123",
  "message": "job submitted Successfully check /status/job_id for results!"
}
```

Rate limit: **5 requests/minute** per client IP.

---

### `GET /status/{job_id}`

Check the status/result of a submitted job.

**Example:**

```bash
curl "http://127.0.0.1:8000/status/a1b2c3d4-..."
```

**Response:**

```json
{
  "job_id": "a1b2c3d4-...",
  "status": "SUCCESS",
  "result": {
    "generated_text": "The capital of France is Paris."
  }
}
```

Completed job results are cached in Redis for **1 hour** to avoid redundant Celery lookups.

---

## 🛠️ Agent Tools

| Tool               | Purpose                                                                 |
|---------------------|--------------------------------------------------------------------------|
| `get_tables`        | Lists all available Supabase tables                                     |
| `get_schema`        | Returns column structure for a given table                              |
| `execute_supabase`  | Executes a **Create/Read-only** Supabase query (destructive ops blocked) |
| `Search`             | Searches Wikipedia and returns summaries for top matches                |
| `Calculator`        | Performs add/subtract/multiply/divide operations                        |

The agent follows a strict workflow when interacting with the database:
1. Call `get_tables()` to confirm/correct the table name (handles typos/casing/pluralization)
2. Call `get_schema()` to confirm column names and types
3. Adapt the user's input to match the schema
4. Call `execute_supabase()` to run the final query

---

## 🔁 Reliability Features

- **Automatic retries:** Failed Celery tasks retry up to 3 times with exponential backoff
- **Dead Letter Queue (DLQ):** Tasks that exhaust all retries are pushed to a `dlq:run_qwen` Redis list for manual inspection instead of being silently dropped
- **Idempotency:** Duplicate `/generate` requests with the same idempotency key return the original job instead of creating a new one
- **Tracing:** Every LLM call and tool call is logged to `agent_trace.jsonl` for debugging

---

## 🧩 Tech Stack

- [LangGraph](https://github.com/langchain-ai/langgraph) — agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) + [Ollama](https://ollama.com/) — local LLM inference (`qwen2.5:14b`)
- [FastAPI](https://fastapi.tiangolo.com/) — HTTP API
- [Celery](https://docs.celeryq.dev/) — distributed task queue
- [Upstash Redis](https://upstash.com/) — broker, result backend, caching
- [Supabase](https://supabase.com/) — Postgres database backend
- [slowapi](https://github.com/laurentS/slowapi) — rate limiting

---

## ⚠️ Notes

- The agent's database permissions are intentionally restricted to **Create** and **Read** — update/delete operations are blocked at both the prompt-instruction and code level as a safety measure.
- `execute_supabase` uses `eval()` with a restricted global namespace; treat this as a development-stage safeguard rather than a hardened security boundary, and avoid exposing it to untrusted input in production.

---
